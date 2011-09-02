-- Copyright © 2011 Tomasz Olejniczak <tomek.87@poczta.onet.pl>
--
-- This package is free software; you can redistribute it and/or modify
-- it under the terms of the GNU General Public License as published by
-- the Free Software Foundation; version 2 dated June, 1991.
--
-- This package is distributed in the hope that it will be useful, but
-- WITHOUT ANY WARRANTY; without even the implied warranty of
-- MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
-- General Public License for more details.

-- TODO: A jedna tabela (np. w getHypothesis lepiej sie sprawdza)

create table fiches (
	position integer not null auto_increment primary key,
	fiche varchar(40) not null,
	work varchar(50),
	bookmark datetime,
	comment varchar(50)
);

create table pages (
	fiche varchar(40) not null primary key,
	page integer not null,
	line integer,
	comment varchar(50)
);

create table actual_entries (
	fiche varchar(40) not null primary key,
	entry varchar(40) not null,
	comment varchar(50)
);

create table original_entries (
	fiche varchar(40) not null primary key,
	entry varchar(40) not null,
	comment varchar(50)
);

create table hypotheses (
	fiche varchar(40) not null primary key,
	entry_hypothesis varchar(40) not null,
	comment varchar(50)
);

create table entry_prefixes (
	fiche varchar(40) not null,
	prefix varchar(40) not null,
	comment varchar(50),
	primary key (fiche, prefix)
);

