## NSW Case Law Database
This project is aimed at buildng a public and programmable database for NSW case law. There is of course a public database for this, in the form of NSW Caselaw as well as austlii and jade.io. However, they do not offer any direct api, meaning we can't make queries beyond what is given in the advanced search options and we cannot achive more complex analysis of the data. 

It is still early days, so there is only a very limited amount of things we can actuall do with the database. The most advanced area of the database is in the Tree (disputes between neighbours) jurisdiction, this is because it's an easy place to start, the law is simple and it represents a sizeable portion of the case law in nsw. 

We can already make queries against this data to find the most common issues in a given area of law. For example we can find the most commonly occuring issues related to torts in NSW, which seem to be:

Using the following query:
```
WITH torts_table AS(
	SELECT case_law.case_id, catchwords.catchword
	FROM case_law
	JOIN catchwords_case_law ON (catchwords_case_law.case_id = case_law.case_id)
		JOIN catchwords ON (catchwords_case_law.catchword_id = catchwords.catchword_id)
	WHERE catchwords.catchword = 'tort' OR catchwords.catchword = 'torts'
)
SELECT catchwords.catchword, COUNT(catchwords.catchword)
FROM torts_table
JOIN catchwords_case_law ON (catchwords_case_law.case_id = torts_table.case_id)
	JOIN catchwords ON (catchwords_case_law.catchword_id = catchwords.catchword_id)
WHERE catchwords.catchword != 'tort' AND catchwords.catchword != 'torts'
GROUP BY catchwords.catchword
ORDER BY COUNT(catchwords.catchword) DESC
LIMIT 10;
```

"negligence"	911
"damages"	256
"defamation"	237
"causation"	188
"duty of care"	166
"contributory negligence"	162
"personal injury"	148
"motor vehicle accident"	133
"assessment of damages"	64
"evidence"	61

Or Maybe more usefully, we can find lawyers who have had the most experience in a particular area of law (for now, that particular area better be tree disputes):

```
WITH tree_table AS(
	SELECT case_law.citation, case_law.case_link, solicitors.solicitor, catchwords.catchword
	FROM case_law
	JOIN catchwords_case_law ON (catchwords_case_law.case_id = case_law.case_id)
		JOIN catchwords ON (catchwords_case_law.catchword_id = catchwords.catchword_id)
	JOIN solicitors_case_law ON (case_law.case_id = solicitors_case_law.case_id)
		JOIN solicitors ON (solicitors_case_law.solicitor_id = solicitors.solicitor_id)
	WHERE catchwords.catchword like '%trees (disputes between neighbours)%'
	AND solicitors.solicitor != 'solicitors'
	AND solicitors.solicitor != 'solicitor'
)
SELECT solicitor, COUNT(solicitor) FROM tree_table 
GROUP BY solicitor
ORDER BY COUNT(solicitor) DESC
LIMIT 10;
```
"n/a"	12
"mclachlan chilton"	8
"litigant in person"	6
"mr p mitchell (solicitor)"	4
"woolf associates"	4
"johnsons solicitors"	4
"connor & co lawyers"	3
"apex planning and environment law"	2
"hones lawyers"	2
"colin biggers & paisley lawyers"	2

Or for barristers:
```
WITH tree_table AS(
	SELECT case_law.citation, case_law.case_link, counsel.counsel, catchwords.catchword
	FROM case_law
	JOIN catchwords_case_law ON (catchwords_case_law.case_id = case_law.case_id)
		JOIN catchwords ON (catchwords_case_law.catchword_id = catchwords.catchword_id)
	JOIN counsel_case_law ON (case_law.case_id = counsel_case_law.case_id)
		JOIN counsel ON (counsel.counsel_id = counsel_case_law.counsel_id)
	WHERE catchwords.catchword = 'trees (disputes between neighbours)'
)
SELECT counsel, COUNT(counsel) FROM tree_table 
GROUP BY counsel
ORDER BY COUNT(counsel) DESC
LIMIT 10;
```

"litigant in person"	69
"litigants in person"	40
"agent"	15
"solicitor"	4
"no appearance"	3
"n hammond"	3
"l walsh"	2
"j shelly and a shelley"	2
"a dimitropoulos"	2
"g jones"	2

Obvciously there is a lot more that should go into deciding upon a lawyer (especially in a jurisdiction like this where decisions are often made out of court through alternative dispute resolution). The data is also far from perfect, j shelly and a shelley are two self represented litigants a dimitropoulos is an agent acting as counsel, both of these things are quite common occurences in this jurisdiction, but it shows that the data set needs more work. 

Nonetheless, it's clear from these examples how this database might be valuable in the future. 

## How to access the database
The database itself is accessible here: https://mega.nz/file/9gxCDCZb#M6jRrnXc0vJqozwc6cfziw8tgtXJ4P8C9ckvcpbuuKg
Because it is so large I am only updating it locally for the moment, the version available in the link above was last updated 02/05/2021.

You will need to create a new database in postgres and then execute the following command:
```
psql -h <hostname> -d <database_name> -U <user_name> -p 5432 -a -q -f
<path to database.sql file>
```
If you would like to work on the code simply clone from this github. To connect to your version of the database add a new file to the core code named "secret_things.py" and add your database information.

