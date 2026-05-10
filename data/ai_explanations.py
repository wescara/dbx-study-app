"""
AI-Generated explanations for Databricks exam questions.
Only includes explanations for questions with N/A explanations in source (40 total).
Questions with existing explanations (51 total) are preserved by the parser.
"""

EXPLANATIONS = {
    1768: "Pull is the Git operation used to fetch and integrate changes from the remote repository into the local copy. Unlike Clone (which creates an initial copy) or Push (which sends changes upstream), Pull specifically updates your local repo with remote changes.",
    
    1770: "Pull is the Git operation used to fetch and integrate changes from the remote repository into the local copy. Unlike Clone (which creates an initial copy) or Push (which sends changes upstream), Pull specifically updates your local repo with remote changes.",
    
    1771: "Cluster virtual machines are part of the data plane and run in the customer's cloud account. The Databricks web application and other services run in the control plane managed by Databricks.",
    
    1773: "Delta Lake is built on Parquet (columnar format), not XML. Parquet is the standard data format that Delta Lake uses, along with transaction logs to provide ACID guarantees, time travel, and audit history.",
    
    1775: "To keep only employees with salary > 3000, you must DELETE rows where salary <= 3000. Option E correctly specifies this condition, removing all employees with salaries of 3000 or less.",
    
    1776: "Python requires '==' for equality comparison in conditionals, not '='. Option E fixes both the comparison operator and includes proper spacing.",
    
    1778: "MERGE INTO is the command that prevents duplicate inserts. It allows conditional inserts, updates, and deletes based on matching criteria, making it ideal when you need to avoid duplicate records.",
    
    1781: "The correct syntax is 'CREATE FUNCTION name(params) RETURNS type RETURN expression;'. Option D matches this pattern exactly, using proper keywords and spacing.",
    
    1787: "Auto Loader monitors a source directory for new files and ingests only newly arrived files on each run, automatically skipping files processed in previous runs—enabling efficient incremental data loading.",
    
    1793: "SHALLOW CLONE shares underlying data files with the source table (saving storage) while creating independent metadata, making it ideal for quick copies and testing.",
    
    1794: "SQL warehouses are the compute resources available in Databricks SQL, replacing traditional multi-node clusters. They're optimized for SQL workloads with automatic scaling and spot instance support.",
    
    1795: "Auto Stop automatically pauses SQL warehouses when idle for a configured duration, minimizing running time and costs without manual intervention. This is an automatic cost-saving feature.",
    
    1796: "OPTIMIZE compacts small data files into larger ones for better query performance. Unlike VACUUM which deletes unused files, OPTIMIZE reorganizes existing data for efficiency.",
    
    1799: "The Databricks web application runs in the control plane (Databricks-managed infrastructure), not in the customer's cloud account. The control plane hosts UI, services, and cluster coordination.",
    
    1803: "External tables drop only metadata; data files remain in external storage. Managed tables drop both metadata and delete the data files from the managed warehouse location.",
    
    1805: "Bronze layer tables maintain raw, unprocessed data ingested directly from source systems. They form the foundation of the medallion architecture, preserving original data for potential recovery and reprocessing.",
    
    1807: "SMS is not supported as an alert destination in Databricks SQL. Supported destinations include Slack, Webhook, Microsoft Teams, and Email for notifications.",
    
    1808: "Email notifications can be configured at the job level to alert team members of job completion status. Settings are available in the job configuration page, not per-notebook or per-task.",
    
    1810: "Cron syntax allows data engineers to specify complex job schedules using expressions like '0 9 * * *' (run daily at 9 AM). This enables flexible, recurring scheduling for production workflows.",
    
    1812: "Data Explorer is the Databricks UI component used to manage permissions on tables and databases. It provides a visual interface for granting and revoking access to data objects.",
    
    1813: "GRANT ALL PRIVILEGES ON TABLE employees TO hr_team grants complete access including SELECT, INSERT, UPDATE, and DELETE. This is the correct syntax for full table permissions.",
    
    1814: "MODIFY privilege grants the ability to insert (add), update (modify), and delete data from a table. It encompasses all data modification operations while excluding structural changes like ALTER.",
    
    1820: "The %python magic command at the start of a cell overrides the default notebook language. This allows running Python code in SQL notebooks, similar to %sql for SQL notebooks.",
    
    1821: "Databricks Repos supports Git branch management, history tracking, merge conflict resolution, and version restoration. These features make it superior to notebook versioning for collaborative development.",
    
    1822: "Databricks SQL provides a data warehousing experience with optimized clusters for SQL queries. It delivers performance tuning and SQL-specific features like auto-scaling and query optimization.",
    
    1823: "VACUUM respects the retention threshold (default 7 days). Files older than the threshold are deleted, while newer files are kept. This ensures long-running queries aren't interrupted.",
    
    1828: "Managed tables store data files in the warehouse location. When dropped, both metadata and data files are deleted. This is the default table type in Databricks.",
    
    1834: "USING CSV specifies the data source format when creating a table from CSV files. Combined with OPTIONS, it configures parsing behavior like delimiters and headers.",
    
    1835: "CREATE SCHEMA (or CREATE DATABASE) creates a database/schema for organizing tables. It's distinct from defining table schema (columns), which is specified in CREATE TABLE.",
    
    1837: "INSERT INTO is the standard SQL command to add rows to a table. Option D uses the correct syntax for appending new records.",
    
    1846: "Gold tables provide business-level aggregations used for dashboards, reports, analytics, and ML models. They're the output layer of the medallion architecture.",
    
    1849: "Query schedules are set from the query page in Databricks SQL, enabling automatic refresh intervals. This maintains fresh data in scheduled dashboards.",
    
    1850: "Delta Live Tables is the declarative framework for building reliable ETL pipelines with automatic dependency tracking and built-in data quality validation.",
    
    1852: "Job Repair reruns only failed tasks in a job, avoiding redundant execution of successful tasks. This minimizes total execution time for large jobs.",
    
    1853: "Email notifications for job failures are configured in the job configuration page. Team members can be notified of specific failure events.",
    
    1855: "Task dependencies are configured via the 'Depends On' field in task settings. This creates the directed acyclic graph (DAG) for job orchestration.",
    
    1856: "Data Explorer provides the UI for managing table permissions including revoking access. It's the primary tool for access control management.",
    
    1857: "USAGE privilege is required but has no inherent permissions; it's a prerequisite for any action on the database. Without USAGE, other privileges are ineffective.",
    
    1858: "Table ownership is changed in Data Explorer's table page using the Owner field. Each table can have a single owner with full control.",
    
    1859: "Commit & Push saves local changes to the remote repository. Commit records changes locally, while Push uploads them to remote Git—both are needed for remote synchronization.",
}

