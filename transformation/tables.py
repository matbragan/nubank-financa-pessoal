import duckdb


def run_scripts(con, **kwargs):
    for key in kwargs:
        con.sql(kwargs[key])


def extract(con):
    drop = "drop table if exists original_extract;"

    schema = """
        create table original_extract (
            date date
        ,   value double
        ,   id varchar
        ,   description varchar
        );
    """

    copy = "copy original_extract from 'data/extracts/*.csv';"

    query = """
        create or replace table extract as (
        select 
            id
        ,   date as data
        ,	if(position('-' in description) > 0, left(description, position(' -' in description) - 1), description) as categoria
        ,	value as valor
        ,	description as descricao
        from 
            original_extract
        );
    """

    run_scripts(con, drop=drop, schema=schema, copy=copy, query=query)


def invoice(con):
    drop = "drop table if exists original_invoice;"

    schema = """
        create table original_invoice (
            date date
        ,   category varchar
        ,   title varchar
        ,   value double
        );
    """

    copy = "copy original_invoice from 'data/invoices/*.csv';"

    query = """
        create or replace table invoice as (
        select 
            date as data
        ,	category as categoria
        ,	value as valor
        ,	title as descricao
        from 
            original_invoice
        where 
            year(date) >= 2024
        );
    """

    run_scripts(con, drop=drop, schema=schema, copy=copy, query=query)


def execute():
    con = duckdb.connect(database='finance.db')
    
    extract(con)
    invoice(con)
    
    con.close()
