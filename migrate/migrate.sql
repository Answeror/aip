create table entry_ (
    id integer not null,
    md5 varchar(128),
    ctime datetime,
    primary key (id),
    unique (md5)
);
insert into entry_ (md5, ctime)
select t.md5, t.ctime
from (
    select p1.md5 as md5, min(p1.ctime) as ctime
    from post as p1
    group by p1.md5
) as t;
alter table entry rename to entry_old;
alter table entry_ rename to entry;

create table plus_ (
    user_id integer not null, 
    entry_id integer not null, 
    ctime datetime, 
    primary key (user_id, entry_id), 
    foreign key(user_id) references user (id), 
    foreign key(entry_id) references entry (id)
);
insert into plus_ (user_id, entry_id)
select p1.user_id, e1.id
from plus as p1 inner join entry as e1 on p1.entry_id = e1.id;
drop table plus;
alter table plus_ rename to plus;
create index ix_plus_ctime on plus (ctime);

drop table entry_old;
create unique index ix_entry_md5 on entry (md5);
create index ix_entry_ctime on entry (ctime);

create table post_ (
    id integer not null, 
    image_url text, 
    width integer, 
    height integer, 
    rating varchar(16), 
    score float, 
    preview_url text, 
    sample_url text, 
    ctime datetime, 
    mtime datetime, 
    post_url text, 
    entry_id integer not null, 
    primary key (id), 
    foreign key(entry_id) references entry (id),
    unique (post_url)
);
insert into post_ (
    image_url, 
    width, 
    height, 
    rating, 
    score, 
    preview_url, 
    sample_url, 
    ctime, 
    post_url, 
    entry_id
) select 
    p1.image_url, 
    p1.width, 
    p1.height, 
    p1.rating, 
    p1.score, 
    p1.preview_url, 
    p1.sample_url, 
    p1.ctime, 
    p1.post_url, 
    e1.id
from post as p1 inner join entry as e1 on p1.md5 = e1.md5;
drop table post;
alter table post_ rename to post;
create index ix_post_entry_id on post (entry_id);
create index ix_post_ctime on post (ctime);
create unique index ix_post_post_url on post (post_url);

alter table tagged add entry_id integer;
update tagged
set entry_id = (
    select p1.entry_id
    from post as p1
    where tagged.post_id = p1.id
);
create index ix_tagged_entry_id on tagged (entry_id);

create table tagged_ (
    post_id integer not null, 
    tag_id integer not null, 
    entry_id integer not null,
    primary key (post_id, tag_id), 
    foreign key(post_id) references post (id), 
    foreign key(tag_id) references tag (id),
    foreign key(entry_id) references entry (id)
);
insert into tagged_ (post_id, tag_id, entry_id)
select t1.post_id, t1.tag_id, p1.entry_id
from tagged as t1 inner join post as p1 on t1.post_id = p1.id;
drop table tagged;
alter table tagged_ rename to tagged;
create index ix_tagged_entry_id on tagged (entry_id);
create index ix_tagged_entry_id_tag_id on tagged (entry_id, tag_id);
