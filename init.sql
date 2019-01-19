CREATE TABLE images (
	id uuid NOT NULL DEFAULT uuid_generate_v4(),
	nid int8 NOT NULL,
	"name" varchar NOT NULL,
	description text NOT NULL,
	uri varchar NOT NULL,
	width int4 NOT NULL,
	height int4 NOT NULL,
	"type" varchar NOT NULL,
	"time" timestamp NOT NULL,
	all_data jsonb NOT NULL,
	stored_uri varchar NOT NULL,
	CONSTRAINT images_pk PRIMARY KEY (id)
);