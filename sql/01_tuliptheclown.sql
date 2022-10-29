CREATE DATABASE TULIPTHECLOWN;
CREATE USER 'tuliptheclown';
SET PASSWORD FOR 'tuliptheclown' = PASSWORD('password');
GRANT ALL PRIVILEGES ON TULIPTHECLOWN.* TO 'tuliptheclown'@'%';

USE TULIPTHECLOWN;

CREATE TABLE Contact (
       contact_id BINARY(16) PRIMARY KEY,
       name_ VARBINARY(64) NOT NULL,
       xor_key VARBINARY(8) NOT NULL,
       contact_type INTEGER NOT NULL,
       phone_or_email VARCHAR(128) NOT NULL
);

CREATE TABLE Message (
       message_key INTEGER AUTO_INCREMENT,
       contact_id BINARY(16) NOT NULL,
       message VARBINARY(8192) NOT NULL,
       xor_key BINARY(16) NOT NULL,
       creation_time DATETIME NOT NULL,
       PRIMARY KEY (message_key),
       FOREIGN KEY(contact_id) REFERENCES Contact(contact_id)
);
