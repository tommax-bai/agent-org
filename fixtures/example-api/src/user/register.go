package user

import (
	"database/sql"
	"errors"
)

type User struct {
	ID    int64
	Email string
	Hash  string
}

func Register(db *sql.DB, email, password string) (*User, error) {
	if email == "" {
		return nil, errors.New("email required")
	}
	// TODO: insert into users(email, hash). currently NO unique check on email.
	_, err := db.Exec("INSERT INTO users(email, hash) VALUES (?, ?)", email, password)
	if err != nil {
		return nil, err
	}
	return &User{Email: email}, nil
}
