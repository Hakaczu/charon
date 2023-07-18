CREATE DATABASE IF NOT EXISTS charon;

USE charon;

CREATE TABLE IF NOT EXISTS data_source(
	id integer NOT NULL AUTO_INCREMENT,
	url varchar(250) NOT NULL,
	name varchar(250) NOT NULL,
	PRIMARY KEY(ID)
);

CREATE TABLE IF NOT EXISTS currencies(
	id integer NOT NULL AUTO_INCREMENT,
	name varchar(250) NOT NULL,
	code varchar(3) NOT NULL,
	PRIMARY KEY(ID)
);

CREATE TABLE IF NOT EXISTS rates(
	id integer NOT NULL AUTO_INCREMENT,
	currency_id integer NOT NULL,
	data_source_id integer NOT NULL,
	mid_rate decimal(10,6) NOT NULL,
	PRIMARY KEY(id),
	CONSTRAINT FK_currency_rates FOREIGN KEY (currency_id) REFERENCES currencies(id),
	CONSTRAINT FK_data_source_rates FOREIGN KEY (data_source_id) REFERENCES data_source(id)
);