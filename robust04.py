import string
printable = set(string.printable)
printable.remove("\n")
printable.remove("\t")
printable.remove("\r")
import os
import shlex
import subprocess
import sys
import re

from searcher import *
import searcher

import nltk
nltk.download('punkt')

import nltk.data
tokenizer = nltk.data.load('tokenizers/punkt/english.pickle')


def clean_html(html):
    """
    Copied from NLTK package.
    Remove HTML markup from the given string.
    :param html: the HTML string to be cleaned
    :type html: str
    :rtype: str
    """

    # First we remove inline JavaScript/CSS:
    cleaned = re.sub(r"(?is)<(script|style).*?>.*?(</\1>)", "", html.strip())
    # Then we remove html comments. This has to be done before removing regular
    # tags since comments can contain '>' characters.
    cleaned = re.sub(r"(?s)<!--(.*?)-->[\n]?", "", cleaned)
    # Next we can remove the remaining tags:
    cleaned = re.sub(r"(?s)<.*?>", " ", cleaned)
    # Finally, we deal with whitespace
    cleaned = re.sub(r"&nbsp;", " ", cleaned)
    cleaned = re.sub(r"  ", " ", cleaned)
    cleaned = re.sub(r"  ", " ", cleaned)
    return cleaned.strip()

def get_qid2query(ftopic):
    qid2query = {}
    f = open(ftopic)
    query_tag = "title"
    empty = False
    for l in f:
        if empty == True:
            qid2query[qid] = l.replace("\n", "").strip()
            empty = False
        ind = l.find("Number: ")
        if ind >= 0:
            qid = l[ind+8:-1]
            qid = str(int(qid))
        ind = l.find("<{}>".format(query_tag))
        if ind >= 0:
            query = l[ind+8:-1].strip()
            if len(query) == 0:
                empty = True
            else:
                qid2query[qid] = query
    return qid2query

def parse_doc_from_index(doc):
    return doc

def search_document(searcher, prediction_fn, qid2text, output_fn, qid2reldocids, K=100):
    # f = open(prediction_fn, "w")
    out = open(output_fn, "w")
    method = "rm3"
    for qid in qid2text:
        a = qid2text[qid]
        hits = searcher.search(JString(a), K)
        for i in range(len(hits)):
            sim = hits[i].score
            docno = hits[i].docid
            label = 1 if qid in qid2reldocids and docno in qid2reldocids[qid] else 0
            b = parse_doc_from_index(hits[i].content)
            b = "".join(filter(lambda x: x in printable, b))
            clean_b = clean_html(b)
            sent_id = 0
            for sentence in tokenizer.tokenize(clean_b):
                sentno = docno + '_'+ str(sent_id)
                # f.write("{} 0 {} 0 {} {}\n".format(qid, sentno, sim, method))
                out.write("{}\t{}\t{}\t{}\t{}\t{}\n".format(label, \
                    sim, a, sentence, qid, sentno))
                out.flush()
                sent_id += 1
    # f.close()
    out.close()

def get_qid2reldocids(fqrel):
    f = open(fqrel)
    qid2reldocids = {}
    for l in f:
        qid, _, docid, score = l.replace("\n", "").strip().split()
        if score != "0":
            if qid not in qid2reldocids:
                qid2reldocids[qid] = set()
            qid2reldocids[qid].add(docid)
    return qid2reldocids

def cal_score(fn_qrels="../Anserini/src/main/resources/topics-and-qrels/qrels.robust2004.txt", prediction="score.txt"):
    cmd = "/bin/sh run_eval_new.sh {} {}".format(prediction, fn_qrels)
    pargs = shlex.split(cmd)
    p = subprocess.Popen(pargs, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    pout, perr = p.communicate()
    print("running {}".format(cmd))
    if sys.version_info[0] < 3:
        lines = pout.split('\n')
    else:
        lines = pout.split(b'\n')
    Map = float(lines[0].strip().split()[-1])
    Mrr = float(lines[1].strip().split()[-1])
    P20 = float(lines[2].strip().split()[-1])
    P30 = float(lines[3].strip().split()[-1])
    NDCG20 = float(lines[4].strip().split()[-1])
    print(Map)
    print(Mrr)
    print(P30)
    print(P20)
    print(NDCG20)
    return Map, Mrr, P30, P20, NDCG20

if __name__ == '__main__':
    fqrel = "../src/main/resources/topics-and-qrels/qrels.robust2004.txt"
    qid2reldocids = get_qid2reldocids(fqrel)
    ftopic = "../src/main/resources/topics-and-qrels/topics.robust04.301-450.601-700.txt"
    qid2text = get_qid2query(ftopic)
    prediction_fn = "predict_robust04_bm25.txt"
    output_fn = "robust04_bm25.txt"
    index_path="/tuna1/indexes/lucene-index.robust04.pos+docvectors+rawdocs"
    searcher = build_searcher(index_path=index_path,rm3=True)
    # searcher = build_searcher()
    search_document(searcher, prediction_fn, qid2text, output_fn, qid2reldocids)
    # cal_score(prediction=prediction_fn)
