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
	fiche varchar(60) not null,
	work varchar(50),
	firstWordPage integer,
	lastWordPage integer,
	matrixNumber integer,
	matrixSector char(1),
	editor varchar(10),
	bookmark datetime,
	comment varchar(50)
);

create index ficheIndex on fiches(fiche);

create table pages (
	fiche varchar(60) not null primary key,
	page integer not null,
	comment varchar(50)
);

create table linesIndex (
	fiche varchar(60) not null primary key,
	line integer not null,
	comment varchar(50)
);

create table actual_entries (
	fiche varchar(60) not null primary key,
	entry varchar(40) not null,
	comment varchar(50)
);

create table original_entries (
	fiche varchar(60) not null primary key,
	entry varchar(40) not null,
	comment varchar(50)
);

create table hypotheses (
	fiche varchar(60) not null primary key,
	entry_hypothesis varchar(40) not null,
	comment varchar(50)
);

create table entry_prefixes (
	fiche varchar(60) not null,
	prefix varchar(40) not null,
	comment varchar(50),
	primary key (fiche, prefix)
);

create table fiche_entries (
	fiche varchar(60) not null,
	pageNo integer,
	lineNo integer,
	entryBegin varchar(100),
	entryBeginLine integer,
	entryBeginWord integer,
	entryBeginChar integer,
	entryEnd varchar(100),
	entryEndLine integer,
	entryEndWord integer,
	entryEndChar integer,
	comment varchar(50)
);

create table text_entries (
	fiche varchar(60) not null,
	entry varchar(100) not null,
	comment varchar(50)
);

create view entries as
	select position, f.fiche, entry
	from fiches f left join actual_entries e
	on f.fiche = e.fiche
	where entry is not null
	order by position;

delimiter /
create procedure delete_entry(position integer)
begin
	delete from original_entries where fiche in (select f.fiche from fiches f where f.position = position);
	delete from actual_entries where fiche in (select f.fiche from fiches f where f.position = position);
end;
/
delimiter ;

delimiter /
create procedure delete_entries(fromm integer, too integer)
begin
	delete from original_entries where fiche in (select f.fiche from fiches f where f.position >= fromm and f.position <= too);
	delete from actual_entries where fiche in (select f.fiche from fiches f where f.position >= fromm and f.position <= too);
end;
/
delimiter ;

