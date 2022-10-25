CREATE DATABASE TULIPTHECLOWN;
CREATE USER 'tuliptheclown';
SET PASSWORD FOR 'tuliptheclown' = PASSWORD('password');
GRANT ALL PRIVILEGES ON TULIPTHECLOWN.* TO 'tuliptheclown'@'%';

USE TULIPTHECLOWN;

CREATE TABLE Contact (
       contact_id BINARY(16) PRIMARY KEY,
       contact_type INTEGER NOT NULL,
       phone_or_email VARCHAR(128)
);

CREATE TABLE Message (
       message_id INTEGER AUTO_INCREMENT,
       contact_id BINARY(16) NOT NULL,
       name_str VARCHAR(128) NOT NULL,
       message VARCHAR(4096) NOT NULL,
       creation_time DATETIME NOT NULL,
       PRIMARY KEY (message_id),
       FOREIGN KEY(contact_id) REFERENCES Contact(contact_id)
);
