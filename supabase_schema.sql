BEGIN;

CREATE TABLE alembic_version (
    version_num VARCHAR(32) NOT NULL, 
    CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
);

-- Running upgrade  -> 86a26a697cc9

CREATE TABLE crops (
    id UUID NOT NULL, 
    name VARCHAR(100) NOT NULL, 
    scientific_name VARCHAR(200), 
    description TEXT, 
    image_url VARCHAR(500), 
    PRIMARY KEY (id)
);

CREATE UNIQUE INDEX ix_crops_name ON crops (name);

CREATE TABLE users (
    id UUID NOT NULL, 
    email VARCHAR(255) NOT NULL, 
    username VARCHAR(50) NOT NULL, 
    password_hash VARCHAR(255) NOT NULL, 
    is_active BOOLEAN NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    PRIMARY KEY (id)
);

CREATE UNIQUE INDEX ix_users_email ON users (email);

CREATE UNIQUE INDEX ix_users_username ON users (username);

CREATE TABLE diseases (
    id UUID NOT NULL, 
    crop_id UUID NOT NULL, 
    name VARCHAR(200) NOT NULL, 
    scientific_name VARCHAR(200), 
    description TEXT, 
    severity VARCHAR(20), 
    symptoms JSON, 
    remedies JSON, 
    prevention JSON, 
    PRIMARY KEY (id), 
    FOREIGN KEY(crop_id) REFERENCES crops (id)
);

CREATE INDEX ix_diseases_crop_id ON diseases (crop_id);

CREATE UNIQUE INDEX ix_diseases_name ON diseases (name);

CREATE TABLE predictions (
    id UUID NOT NULL, 
    user_id UUID NOT NULL, 
    image_url VARCHAR(500) NOT NULL, 
    selected_crop VARCHAR(100) NOT NULL, 
    disease_name VARCHAR(200), 
    confidence FLOAT, 
    severity VARCHAR(20), 
    remedies JSON, 
    created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(user_id) REFERENCES users (id)
);

CREATE INDEX ix_predictions_user_id ON predictions (user_id);

INSERT INTO alembic_version (version_num) VALUES ('86a26a697cc9') RETURNING alembic_version.version_num;

-- Running upgrade 86a26a697cc9 -> 1a9664c08f6e

UPDATE alembic_version SET version_num='1a9664c08f6e' WHERE alembic_version.version_num = '86a26a697cc9';

-- Running upgrade 1a9664c08f6e -> 38070dcdab4b

UPDATE alembic_version SET version_num='38070dcdab4b' WHERE alembic_version.version_num = '1a9664c08f6e';

-- Running upgrade 38070dcdab4b -> 36aee3827a3b

UPDATE alembic_version SET version_num='36aee3827a3b' WHERE alembic_version.version_num = '38070dcdab4b';

-- Running upgrade 36aee3827a3b -> 6eb4dbb76fa3

UPDATE alembic_version SET version_num='6eb4dbb76fa3' WHERE alembic_version.version_num = '36aee3827a3b';

-- Running upgrade 6eb4dbb76fa3 -> b488d4617e6c

UPDATE alembic_version SET version_num='b488d4617e6c' WHERE alembic_version.version_num = '6eb4dbb76fa3';

-- Running upgrade b488d4617e6c -> 85c36d0a2e0e

CREATE TABLE drug_predictions (
    id UUID NOT NULL, 
    user_id UUID NOT NULL, 
    smiles VARCHAR(1000) NOT NULL, 
    predicted_class VARCHAR(50) NOT NULL, 
    confidence JSON NOT NULL, 
    note VARCHAR(500), 
    created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(user_id) REFERENCES users (id)
);

CREATE INDEX ix_drug_predictions_user_id ON drug_predictions (user_id);

UPDATE alembic_version SET version_num='85c36d0a2e0e' WHERE alembic_version.version_num = 'b488d4617e6c';

COMMIT;

