(define-module (genenetwork-auth)
  #:use-module (guix)
  #:use-module (guix git-download)
  #:use-module (guix build-system python)
  #:use-module ((guix licenses) #:prefix license:)

  #:use-module (git oid)
  #:use-module (git bindings)
  #:use-module (git reference)
  #:use-module (git repository)


  ;; Packages from guix
  #:use-module (gnu packages check)

  #:use-module (gnu packages python-web)
  #:use-module (gnu packages python-xyz)
  #:use-module (gnu packages python-crypto)

  #:use-module (gnu packages databases)


  ;; Packages from guix-bioinformatics
  #:use-module (gn packages python-web))

(define %source-dir (dirname (dirname (dirname (current-filename)))))

(define (get-commit)
  "Retrieve the commit if the source directory is a repository."
  (if (git-predicate %source-dir)
      (begin (let ((commit #f))
	       (libgit2-init!)
	       (set! commit (oid->string
			     (reference-target
			      (repository-head (repository-open %source-dir)))))
	       (libgit2-shutdown!)
	       commit))
      "NOTAREPOSITORY"))

(define (get-latest-version)
  "Get latest version tag from repository."
  ;; TODO: Implement
  "v0.0.0")

(define vcs-file?
  (or (git-predicate %source-dir)
      (const #t)))

(package
 (name "genenetwork-auth")
 (version (string-append (get-latest-version)
			 "-git-"
			 (substring (get-commit) 0 9)))
 (source (local-file %source-dir "genenetwork-auth-checkout"
		     #:recursive? #t
		     #:select? vcs-file?))
 (build-system python-build-system)
 ;; (inputs (list))
 (native-inputs
  (list python-pytest
	python-pylint))
 (propagated-inputs
  (list python-flask
	python-authlib
	yoyo-migrations
	python-argon2-cffi
	python-email-validator))
 (home-page "https://github.com/genenetwork/gn-auth")
 (synopsis "Authentication and Authorisation server for GeneNetwork services.")
 (description "Authentication and Authorisation server for GeneNetwork services.")
 (license license:agpl3+))
