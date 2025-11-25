CREATE TABLE public.perform_tmp (
	id serial4 NOT NULL,
	club_id int4 NOT NULL,
	user_id int4 NOT NULL,
	title varchar(100) NULL,
	description text NULL,
	perform_date timestamptz NULL,
	booking_price int4 DEFAULT 0 NULL,
	created_at timestamptz DEFAULT now() NULL,
	updated_at timestamptz NULL,
	is_cancelled bool NULL,
	artists jsonb NULL,
	sns_links jsonb NULL,
	onsite_price int4 DEFAULT 0 NULL,
	booking_url varchar(255) NULL,
	CONSTRAINT perform_tmp_pkey PRIMARY KEY (id)
);

ALTER TABLE public.perform_tmp ADD CONSTRAINT perform_tmp_club_id_fkey FOREIGN KEY (club_id) REFERENCES public.club_tb(id);
ALTER TABLE public.perform_tmp ADD CONSTRAINT perform_tmp_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.user_tb(id);


CREATE TABLE public.perform_img_tmp (
	id serial4 NOT NULL,
	perform_id int4 NOT NULL,
	file_path varchar(255) NULL,
	created_at timestamptz DEFAULT now() NULL,
	updated_at timestamptz NULL,
	is_main bool NULL,
	original_name varchar(255) NULL,
	file_size int8 NULL,
	CONSTRAINT perform_img_tmp_pkey PRIMARY KEY (id)
);

ALTER TABLE public.perform_img_tmp ADD CONSTRAINT perform_img_tmp_perform_id_fkey FOREIGN KEY (perform_id) REFERENCES public.perform_tmp(id);