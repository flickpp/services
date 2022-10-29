USE TULIPTHECLOWN;

CREATE TABLE Review (
       review_id BINARY(16) NOT NULL,
       contact_id BINARY(16) NOT NULL,
       review VARBINARY(8192) NOT NULL,
       xor_key BINARY(16) NOT NULL,
       weight TINYINT UNSIGNED NOT NULL,
       response VARBINARY(4096) NULL,
       creation_time DATETIME NOT NULL,
       response_time DATETIME NULL,
       PRIMARY KEY(review_id),
       FOREIGN KEY(contact_id) REFERENCES Contact(contact_id)
);

CREATE TABLE Event (
       event_id BINARY(16) PRIMARY KEY,
       contact_id BINARY(16) NOT NULL,
       review_id BINARY(16) NULL,
       date_ DATE NOT NULL,
       start_time TIME NOT NULL,
       end_time   TIME NOT NULL,
       description VARBINARY(8192) NOT NULL,
       FOREIGN KEY(contact_id) REFERENCES Contact(contact_id),
       FOREIGN KEY(review_id) REFERENCES Review(review_id)
);

