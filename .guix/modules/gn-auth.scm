(define-module (gn-auth)
  #:use-module (guix)
  #:use-module (guix packages)
  #:use-module (guix download)
  #:use-module (guix git-download)
  #:use-module (guix build-system python)
  #:use-module ((guix licenses) #:prefix license:)

  ;; Packages from guix
  #:use-module (gnu packages check)

  #:use-module (gnu packages django)

  #:use-module (gnu packages python-web)
  #:use-module (gnu packages python-xyz)
  #:use-module (gnu packages python-check)
  #:use-module (gnu packages python-crypto)

  #:use-module (gnu packages databases)

  ;; Packages from guix-bioinformatics
  #:use-module (gn packages python-web))

(define %source-dir (dirname (dirname (current-source-directory))))

(define vcs-file?
  (or (git-predicate %source-dir)
      (const #t)))

(define-public gn-auth
  (package
   (name "gn-auth")
   (version "0.1.0-git")
   (source (local-file "../.."
		       "gn-auth-checkout"
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
    (list gunicorn
	  python-flask
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
