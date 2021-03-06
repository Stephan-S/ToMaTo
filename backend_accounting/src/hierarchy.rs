use std::collections::HashMap;
use std::hash::BuildHasherDefault;
use std::sync::{RwLock, RwLockReadGuard};
use std::sync::atomic::{AtomicBool, Ordering};
use std::time::Duration;
use std::fmt::Debug;
use std::mem;

use fnv::FnvHasher;
use sslrpc2::{Client, ClientCloseGuard, KwArgs, ParseValue, ToValue, Error, Value, Args};
use sslrpc2::openssl::ssl::SslContext;
use sslrpc2::openssl::ssl::error::SslError;


use data::RecordType;
use util::{Time, now};

pub type Hash = BuildHasherDefault<FnvHasher>;

#[derive(Debug)]
pub enum HierarchyError {
    NoSuchEntity,
    NoSuchRelation,
    CommunicationError,
}

#[derive(Debug)]
pub enum Service {
    User, Core
}

pub trait Hierarchy: Send + Sync {
    fn get(&self, child_type: RecordType, parent_type: RecordType, child_id: &str) -> Result<Vec<String>, HierarchyError>;
    fn exists(&self, type_: RecordType, id: &str) -> Result<bool, HierarchyError>;
}

type CacheKey = (RecordType, RecordType);
type CacheEntry = RwLock<HashMap<String, (Vec<String>, Time), Hash>>;

pub struct HierarchyCache {
    timeout: Time,
    inner: Box<Hierarchy>,
    cache: HashMap<CacheKey, CacheEntry, Hash>
}

impl HierarchyCache {
    pub fn new(inner: Box<Hierarchy>, timeout: Time) -> Self {
        let mut obj = HierarchyCache {
            timeout: timeout,
            inner: inner,
            cache: HashMap::default()
        };
        for &(child, parent) in &[
            (RecordType::HostElement, RecordType::Element), (RecordType::HostElement, RecordType::Connection),
            (RecordType::HostConnection, RecordType::Connection),
            (RecordType::Element, RecordType::Topology), (RecordType::Connection, RecordType::Topology),
            (RecordType::Topology, RecordType::User), (RecordType::User, RecordType::Organization)
        ] {
            obj.cache.insert((child, parent), RwLock::new(HashMap::default()));
        }
        obj
    }

    pub fn put(&self, child_type: RecordType, child_id: String, parent_type: RecordType, parent_ids: Vec<String>) {
        let group = self.cache.get(&(child_type, parent_type)).expect("No such relation");
        group.write().expect("Lock poisoned").insert(child_id, (parent_ids, now()));
    }
}

impl Hierarchy for HierarchyCache {
    fn get(&self, child_type: RecordType, parent_type: RecordType, child_id: &str) -> Result<Vec<String>, HierarchyError> {
        let now = now();
        let group = match self.cache.get(&(child_type, parent_type)) {
            Some(group) => group,
            None => return Err(HierarchyError::NoSuchRelation)
        };
        {
            let group = group.read().expect("Lock poisoned");
            if let Some(&(ref data, time)) = group.get(child_id) {
                if time + self.timeout > now {
                    return Ok(data.clone());
                }
            }
        }
        warn!("{} of {}/{} unknown, querying", parent_type.name(), child_type.name(), child_id);
        let fresh = try!(self.inner.get(child_type, parent_type, child_id));
        let mut group = group.write().expect("Lock poisoned");
        group.insert(child_id.to_owned(), (fresh.clone(), now));
        Ok(fresh)
    }

    fn exists(&self, type_: RecordType, id: &str) -> Result<bool, HierarchyError> {
        self.inner.exists(type_, id)
    }
}

pub struct DummyHierarchy;

impl Hierarchy for DummyHierarchy {
    fn get(&self, child_type: RecordType, parent_type: RecordType, child_id: &str) -> Result<Vec<String>, HierarchyError> {
        warn!("Dummy hierarchy queried for {} of {}/{}", parent_type.name(), child_type.name(), child_id);
        Ok(Vec::new())
    }

    fn exists(&self, type_: RecordType, id: &str) -> Result<bool, HierarchyError> {
        warn!("Dummy hierarchy queried for existence of {}/{}", type_.name(), id);
        Ok(false)
    }
}

#[allow(dead_code)]
pub struct RemoteHierarchy {
    ssl_context: SslContext,
    user_service_address: String,
    core_service_address: String,
    service_timeout: Duration,
    user_service: RwLock<ClientCloseGuard>,
    user_service_broken: AtomicBool,
    core_service: RwLock<ClientCloseGuard>,
    core_service_broken: AtomicBool,
}

impl RemoteHierarchy {
    pub fn new(ssl_context: SslContext, core_service_address: String, user_service_address: String, service_timeout: Time) -> Result<Self, SslError> {
        let core_service = try!(Client::new(&core_service_address as &str, ssl_context.clone()));
        let user_service = try!(Client::new(&user_service_address as &str, ssl_context.clone()));
        Ok(RemoteHierarchy {
            ssl_context: ssl_context,
            core_service_address: core_service_address,
            user_service_address: user_service_address,
            service_timeout: Duration::from_secs(service_timeout as u64),
            user_service: RwLock::new(user_service),
            user_service_broken: AtomicBool::new(false),
            core_service: RwLock::new(core_service),
            core_service_broken: AtomicBool::new(false)
        })
    }

    fn get_service(&self, type_: RecordType) -> Result<(Service, RwLockReadGuard<ClientCloseGuard>), HierarchyError> {
        Ok(match type_ {
            RecordType::HostElement | RecordType::HostConnection | RecordType::Element | RecordType::Connection | RecordType::Topology => {
                if self.core_service_broken.load(Ordering::Relaxed) {
                    info!("Reconnecting to core service...");
                    let mut core_service = try!(Client::new(&self.core_service_address as &str, self.ssl_context.clone()).map_err(|_| HierarchyError::CommunicationError));
                    mem::swap(&mut core_service, &mut self.core_service.write().expect("Lock poisoned"));
                    core_service.close().expect("Failed to close");
                    self.core_service_broken.store(false, Ordering::Relaxed);
                }
                (Service::Core, self.core_service.read().expect("Lock poisoned"))
            },
            RecordType::User | RecordType::Organization => {
                if self.user_service_broken.load(Ordering::Relaxed) {
                    info!("Reconnecting to user service...");
                    let mut user_service = try!(Client::new(&self.user_service_address as &str, self.ssl_context.clone()).map_err(|_| HierarchyError::CommunicationError));
                    mem::swap(&mut user_service, &mut self.user_service.write().expect("Lock poisoned"));
                    user_service.close().expect("Failed to close");
                    self.user_service_broken.store(false, Ordering::Relaxed);
                }
                (Service::User, self.user_service.read().expect("Lock poisoned"))
            }
        })
    }

    fn call<T: ParseValue + Debug>(&self, service_type: Service, service: RwLockReadGuard<ClientCloseGuard>, method: &str, args: Args) -> Result<T, HierarchyError> {
        match service.call(
            method.to_owned(),
            args.clone(),
            KwArgs::default(),
            Some(self.service_timeout)
        ) {
            Ok(res) => {
                let result = try!(T::parse(res).map_err(|_| HierarchyError::CommunicationError));
                debug!("Remote call succeeded: {}{:?} => {:?}", method, args, result);
                Ok(result)
            },
            Err(Error::Failure(err)) => {
                type Failure = HashMap<String, Value>;
                let err = try!(Failure::parse(err).map_err(|_| HierarchyError::CommunicationError));
                if Some(&Value::String("entity_does_not_exist".to_owned())) == err.get("code") {
                    return Err(HierarchyError::NoSuchEntity);
                }
                warn!("Remote call failed: {}{:?} => {:?}", method, args, err);
                match service_type {
                    Service::Core => self.core_service_broken.store(false, Ordering::Relaxed),
                    Service::User => self.user_service_broken.store(false, Ordering::Relaxed)
                }
                Err(HierarchyError::CommunicationError)
            },
            Err(err) => {
                warn!("Remote call failed: {}{:?} => {:?}", method, args, err);
                match service_type {
                    Service::Core => self.core_service_broken.store(false, Ordering::Relaxed),
                    Service::User => self.user_service_broken.store(false, Ordering::Relaxed)
                }
                Err(HierarchyError::CommunicationError)
            }
        }
    }
}

impl Hierarchy for RemoteHierarchy {
    fn get(&self, child_type: RecordType, parent_type: RecordType, child_id: &str) -> Result<Vec<String>, HierarchyError> {
        let (service_type, service) = try!(self.get_service(child_type));
        let result: Vec<(String, String)> = try!(self.call(service_type, service, "object_parents", vec![to_value!(child_type.name().to_owned()), to_value!(child_id.to_owned())]));
        let mut parents = Vec::with_capacity(result.len());
        for (type_, id) in result {
            if type_ == parent_type.name() {
                parents.push(id);
            }
        }
        Ok(parents)
    }

    fn exists(&self, type_: RecordType, id: &str) -> Result<bool, HierarchyError> {
        let (service_type, service) = try!(self.get_service(type_));
        self.call(service_type, service, "object_exists", vec![to_value!(type_.name().to_owned()), to_value!(id.to_owned())])
    }
}
