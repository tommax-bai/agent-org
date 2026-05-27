package auth

import (
	"errors"
	"net/http"
)

// Login handles user login. Currently uses default HTTP server timeout (30s).
func Login(w http.ResponseWriter, r *http.Request) {
	email := r.FormValue("email")
	password := r.FormValue("password")
	if email == "" || password == "" {
		http.Error(w, "missing credentials", http.StatusBadRequest)
		return
	}
	// TODO: actual auth
	_ = errors.New("not implemented")
	w.WriteHeader(http.StatusOK)
}
