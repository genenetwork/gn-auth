(define-module (gn-auth)
  #:use-module ((gn packages genenetwork)
                #:select (gn-auth) #:prefix gn:)
  #:use-module ((gnu packages check) #:select (python-pylint))
  #:use-module ((gnu packages python-check) #:select (python-mypy))
  #:use-module (guix)
  #:use-module (guix gexp)
  #:use-module (guix packages)
  #:use-module (guix download)
  #:use-module (guix git-download)
  #:use-module ((guix licenses) #:prefix license:))

(define %source-dir (dirname (dirname (current-source-directory))))

(define vcs-file?
  (or (git-predicate %source-dir)
      (const #t)))

(define-public gn-auth
  (package
    (inherit gn:gn-auth)
    (source
     (local-file "../.."
		 "gn-auth-checkout"
		 #:recursive? #t
		 #:select? vcs-file?))))

(define-public gn-auth-all-tests
  (package
    (inherit gn-auth)
    (arguments
     (substitute-keyword-arguments (package-arguments gn-auth)
       ((#:phases phases #~%standard-phases)
        #~(modify-phases #$phases
            (add-before 'build 'pylint
              (lambda _
                (invoke "pylint" "main.py" "setup.py" "wsgi.py"
                        "tests" "gn_auth" "scripts")))
            (add-after 'pylint 'mypy
              (lambda _
                (invoke "mypy" ".")))))))
    (native-inputs
     (modify-inputs (package-native-inputs gn-auth)
       (prepend python-mypy)
       (prepend python-pylint)))))

gn-auth
