(define-module (gn-auth)
  #:use-module (guix)
  #:use-module (guix packages)
  #:use-module (guix download)
  #:use-module (guix git-download)
  #:use-module (guix build-system python)
  #:use-module ((guix licenses) #:prefix license:)

  #:use-module (git oid)
  #:use-module (git tag)
  #:use-module (git bindings)
  #:use-module (git reference)
  #:use-module (git repository)


  ;; Packages from guix
  #:use-module (gnu packages check)

  #:use-module (gnu packages django)

  #:use-module (gnu packages python-web)
  #:use-module (gnu packages python-xyz)
  #:use-module (gnu packages python-check)
  #:use-module (gnu packages python-crypto)

  #:use-module (gnu packages databases)

  ;; Packages from guix-bioinformatics
  #:use-module (gnu packages python-web))

(define %source-dir (dirname (dirname (dirname (dirname (dirname (current-filename)))))))

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

(define (list-last lst)
  (let ((len (length lst)))
    (if (> len 0)
	(list-ref lst (- len 1)))))

(define (process-version repo-head tag-vals)
  (let ((version-prefix (list-last (string-split (car tag-vals) #\/)))
	(repo-head-str (oid->string repo-head)))
    (if (zero? (oid-cmp  repo-head
			 (tag-target-id (cdr tag-vals))))
	version-prefix
	(string-append version-prefix "-" (substring repo-head-str 0 8)))))

(define (get-latest-version)
  "Get latest version tag from repository."
  (if (git-predicate %source-dir)
      (let ((%repo #f)
	    (%tags (list))
	    (%repo-head #f))
	(begin (libgit2-init!)
	       (set! %repo (repository-open %source-dir))
	       (set! %repo-head (reference-target (repository-head %repo)))
	       (tag-foreach %repo
			    (lambda (tname tref)
			      (set! %tags (list (cons tname (tag-lookup %repo tref))))
			      0))
	       (libgit2-shutdown!)
	       (if (zero? (length %tags))
		   (string-append "v0.0.0-" (substring (oid->string %repo-head) 0 8))
		   (process-version
		    %repo-head
		    (list-last (sort-list %tags (lambda (item) (error item))))))))
      ;; Figure out a way to get the version in the checkouts when building
      "v0.0.0"))

(define vcs-file?
  (or (git-predicate %source-dir)
      (const #t)))

(define-public gn-auth
  (package
   (name "gn-auth")
   (version (string-append (get-latest-version)
			   "-git-"
			   (substring (get-commit) 0 9)))
   (source (local-file %source-dir "gn-auth-checkout"
		       #:recursive? #t
		       #:select? vcs-file?))
   (build-system python-build-system)
   (arguments
    (list
     #:phases
     #~(modify-phases %standard-phases
		      (replace 'check
			       (lambda _ (invoke "pytest" "-k" "unit_test"))))))
   ;; (inputs (list))
   (native-inputs
    (list python-mypy
	  python-pytest
	  python-pylint
	  python-hypothesis
	  python-pytest-mock
          python-mypy-extensions))
   (propagated-inputs
    (list python-flask
	  python-redis
	  python-authlib
	  python-pymonad
	  yoyo-migrations
	  python-bcrypt ;; remove after removing all references
	  python-mysqlclient
	  python-argon2-cffi
	  python-email-validator))
   (home-page "https://github.com/genenetwork/gn-auth")
   (synopsis "Authentication and Authorisation server for GeneNetwork services.")
   (description "Authentication and Authorisation server for GeneNetwork services.")
   (license license:agpl3+)))

gn-auth
