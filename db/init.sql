CREATE DATABASE emulator;
use emulator;

CREATE TABLE charge_state (
  dpid INT NOT NULL UNIQUE,
  charge INT NOT NULL,
  ts TIMESTAMP NOT NULL
);

CREATE TABLE events (
  dpid INT NOT NULL UNIQUE,
  from_mac VARCHAR(20) NOT NULL,
  to_mac VARCHAR(20) NOT NULL,
  port INT NOT NULL
);
