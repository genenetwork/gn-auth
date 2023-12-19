(define-module (gn-auth)
  #:use-module ((gn packages genenetwork)
                #:select (gn-auth) #:prefix gn:)
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

gn-auth
