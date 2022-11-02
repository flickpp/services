USE KVSTORE;

SET GLOBAL event_scheduler = ON;

CREATE EVENT remove_expired_kv1
    ON SCHEDULE EVERY 1 MINUTE DO
        DELETE FROM KVSTORE.Value where expiry_time < NOW();
