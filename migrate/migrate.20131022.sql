delete from tagged where post_id in (select max(id) from post group by post_url having count(*) > 1);
delete from post where id in (select max(id) from post group by post_url having count(*) > 1);
create unique index ix_post_post_url on post (post_url);
