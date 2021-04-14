#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time, datetime, logging
import pywikibot
import toolforge
from db_handle import *

site = pywikibot.Site()

tf_conn = toolforge.connect("enwiki")

def task_permitted(task_num):
    shutoff_page_title = "User:FireflyBot/shutoff/{}".format(task_num)
    shutoff_page = pywikibot.Page(site, shutoff_page_title)

    return (shutoff_page.get().strip().lower() == "active")

def get_pages_with_pending_revs():
        cur = tf_conn.cursor()
        cur.execute("select page_id,fpp_rev_id from flaggedpage_pending inner join revision on rev_id=fpp_rev_id inner join page on rev_page=page_id")
        return cur.fetchall()

def get_pending_revs_for_db(page_id, last_accepted_rev):
        cur = tf_conn.cursor()
        cur.execute("select rev_id from revision inner join actor on rev_actor=actor_id inner join user on user_id=actor_user left join user_groups on ug_user=user_id where (ug_group='extendedconfirmed' or ug_group='confirmed' or ug_group='autoconfirmed' or ug_group='sysop'or ug_group='bot') and rev_page='{}' and rev_id>{}".format(page_id, last_accepted_rev))
        return [x[0] for x in cur.fetchall()]

def add_rev_to_db(rev_id):
        cur = conn.cursor()
        cur.execute("insert ignore into reviewed_revs (rev_id) values('{}');".format(rev_id))
        conn.commit()

def is_rev_in_db(rev_id):
        cur = conn.cursor()
        ret = cur.execute("select 1 from reviewed_revs where rev_id={}".format(rev_id))
        return (ret > 0)

def get_auto_acceptable_revs(page_id, last_accepted_rev):
        cur = tf_conn.cursor()
        current_rev = last_accepted_rev
        aa_revs = []
        while current_rev is not None:
                cur.execute("select rev_id from revision inner join actor on rev_actor=actor_id inner join user on user_id=actor_user left join user_groups on ug_user=user_id where (ug_group='extendedconfirmed' or ug_group='confirmed' or ug_group='autoconfirmed' or ug_group='sysop'or ug_group='bot') and rev_parent_id='{}' and rev_page='{}'".format(last_accepted_rev, page_id))
                data = cur.fetchone()
                if data is None or len(data) == 0:
                        current_rev = None
                elif (is_rev_in_db(data[0])):
                        current_rev = None
                elif (data[0] == current_rev): # This shouldn't happen, but.... apparently it does now!
                        if current_rev not in aa_revs:
                                aa_revs.append(current_rev)
                        current_rev = None 
                else:
                        current_rev = data[0]
                        aa_revs.append(current_rev)
                        
        return aa_revs

def accept_revision(rev_id):
        csrf = site.get_tokens(["csrf"])['csrf']
        accept_request = pywikibot.data.api.Request(site=site, parameters={'action':'review', 'revid':rev_id, 'comment':'(BOT) Revision should have automatically been accepted as user meets auto-accept threshold. See [[phab:T233561]]', 'token':csrf})
        return accept_request.submit()['review']

def dump_acceptable_rev_onwiki(rev_id):
        page = pywikibot.Page(site, "User:FireflyBot_II/brfa_pc_log")
        text = page.get()
        page.put(newtext="{} - accepting {}\n{}".format(datetime.datetime.now(), rev_id, text), summary="*Logging acceptance of rev [[Special:Diff/{0}|{0}]]".format(rev_id))

def process_buggy_revs():
        for page_id,last_accepted_rev_id in get_pages_with_pending_revs():
                aa_revs = get_auto_acceptable_revs(page_id, int(last_accepted_rev_id))
                for aa_rev in aa_revs:
                        #accept_revision(aa_rev)
                        dump_acceptable_rev_onwiki(aa_rev)
                for rev in get_pending_revs_for_db(page_id, int(last_accepted_rev_id)):
                        add_rev_to_db(rev)

def main(*args):
    if (True):
        process_buggy_revs()
    else:
        logger.info(u"Task not permitted to run - onwiki shutoff bit flipped")

if __name__ == "__main__":
    main()

