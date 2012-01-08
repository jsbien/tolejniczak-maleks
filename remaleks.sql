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

drop table fiches;
drop table pages;
drop table linesIndex;
drop table actual_entries;
drop table original_entries;
drop table hypotheses;
drop table entry_prefixes;
drop table text_entries;
drop table fiche_entries;
drop view entries;
drop procedure delete_entry;
drop procedure delete_entries;

source maleks.sql;

