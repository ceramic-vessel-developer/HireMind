BEGIN;

DROP TABLE IF EXISTS public.results CASCADE;
DROP TABLE IF EXISTS public.cvs CASCADE;
DROP TABLE IF EXISTS public.users CASCADE;


CREATE TABLE public.users
(
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL
);


CREATE TABLE public.cvs
(
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    file_format VARCHAR NOT NULL,
    file_key VARCHAR NOT NULL UNIQUE,

    CONSTRAINT cvs_user_fk
        FOREIGN KEY (user_id)
        REFERENCES public.users (id)
        ON DELETE CASCADE
);


CREATE TABLE public.results
(
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    cv_id INTEGER NOT NULL,
    joint_score DOUBLE PRECISION NOT NULL,
    advice TEXT NOT NULL,

    CONSTRAINT results_user_fk
        FOREIGN KEY (user_id)
        REFERENCES public.users (id)
        ON DELETE CASCADE,

    CONSTRAINT results_cv_fk
        FOREIGN KEY (cv_id)
        REFERENCES public.cvs (id)
        ON DELETE CASCADE
);

COMMIT;