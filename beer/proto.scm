(use-module '{fdweb xhtml texttools})
(use-module '{openlibrary})

(define abbyymakehtml (get-component "../abbyymakehtml"))
(define tmpdir "/tmp/abbyy2html")

(define (showtext olib)
  (let ((path (mkpath tmpdir (string-append olib ".html"))))
    (forkwait abbyymakehtml path)
    (xhtml (filestring path))))

(define (padpageno num)
  (stringout 
    (if (< num 1000) "0")
    (if (< num 100) "0")
    (if (< num 10) "0")
    num))

(define (getbookpath olib)
  (let* ((bookid (olib/get (olib/ref olib) 'ocaid))
	 (metaurl (stringout "http://www.archive.org/download/"
		    bookid "/" bookid "_meta.xml"))
	 (location (get (urlget metaurl) 'location)))
    (if (has-suffix location "_meta.xml")
	(subseq location 0 (- 9))
	location)))

(define (getpageurl olib (pageno #f))
  (let* ((bookid (olib/get (olib/ref olib) 'ocaid))
	 (bookpath (getbookpath olib)))
    (stringout "http://" (urihost bookpath)
      "/BookReader/BookReaderImages.php?"
      "zip=/" (printout (uripath bookpath) "_jp2.zip")
      "&file=" (printout bookid "_jp2/" bookid "_"
		 (if pageno (padpageno pageno) "%%%%")
		 ".jp2&scale=4&rotate=0"))))

