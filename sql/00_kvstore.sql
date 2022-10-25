CREATE DATABASE KVSTORE;
CREATE USER 'kvstore';
SET PASSWORD  FOR 'kvstore' = PASSWORD('password');
GRANT ALL PRIVILEGES ON KVSTORE.* TO 'kvstore'@'%';

USE KVSTORE;
CREATE TABLE Value (
       key_id BINARY(16) PRIMARY KEY,
       xor_key BINARY(32) NOT NULL,
       value_str VARCHAR(512) NOT NULL,
       expiry_time DATETIME NOT NULL
);
