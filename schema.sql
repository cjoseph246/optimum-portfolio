drop table if exists entries;
create table entries (
  id integer primary key autoincrement,
  first integer not null,
  second integer not null,
  third integer not null,
  fourth integer,
  fifth integer
);