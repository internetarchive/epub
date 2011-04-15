(use-module '{texttools optimize})
(use-module '{domutils domutils/index})
(use-module '{sbooks sbooks/db sbooks/parse sbooks/tools})

(config! 'dompool (make-mempool "books" @3333/0 (* 1024 1024)))

(optimize! '{sbooks sbooks/parse sbooks/tools sbooks/autotag domutils domutils/index})

(define (index-node-for-lineup node index)
  (let* ((text (dom/textify node))
	 (spans (tryif (> (isspace% text) 0)
		  (elts (textslice text #((ispunct+) {(eos) (spaces)})))))
	 (wordv (words->vector spans))
	 (frags (seq->phrase (vector->frags wordv 2 #f))))
    (store! node 'frags frags)
    (add! index frags node)))

(define (lineup-index doc (rare 3))
  (let ((table (get doc 'node:index))
	(textnodes (dom/find doc "P")))
    (when (fail? table)
      (set! table (make-hashtable))
      (store! doc 'node:index table))
    (store! doc 'textnodes textnodes)
    (index-node-for-lineup textnodes table)
    (do-choices (key (getkeys table))
      (when (<= (choice-size (get table key)) rare)
	(add! doc 'rare key)))
    table))

(define (lineup-scores node doc (rare #f))
  (let ((index (get doc 'node:index))
	(scores (make-hashtable)))
    (do-choices (key (if rare
			 (intersection (get doc 'rare) (get node 'frags))
			 (get node 'frags)))
      (hashtable-increment! scores
	  (get index key)
	(/~ 1.0 (* (choice-size (get index key))
		   (choice-size (get index key))))))
    scores))

(define (lineup0 doc1 doc2)
  (let ((map (make-hashtable)))
    (do-choices (node (get doc1 'textnodes))
      (let* ((scores (lineup-scores node doc2 #t))
	     (analog (table-max scores)))
	(when (and (singleton? analog)
		   (identical? (table-max (lineup-scores analog doc1 #t))
			       node))
	  (store! map node analog))))
    map))

(optimize!)

(define files
  (pick (pick (getfiles (getcwd)) has-suffix ".html") string-contains? "OL"))

(define docs
  (for-choices (f files) (sbooks/prepare (sbooks/parse-file f))))

(lineup-index docs)

(define adoc (pick-one docs))
(define anode (pick-one (get adoc 'textnodes)))
(define bnode (pick-one (get adoc 'textnodes)))
(define cnode (pick-one (get adoc 'textnodes)))
(define bdoc (pick-one (difference docs adoc)))
(define cdoc (pick-one (difference docs adoc bdoc)))