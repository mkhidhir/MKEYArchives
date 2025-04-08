/*********************************
	SAL-9279-Positions - TASK REFERENCE

	Prospect needs to see all vessels that passed this area in an easy to read format. 
	They did not specific any specific parameters so it would be good to guide them by adding vessel type, size, and whatever else you think could be relevant. 

	It would be good if you can share the full extraction and a separate copy with limited rows so I can share with them as a sample. Also, if you can give me an indication whether the quantity of data is a lot, it would 

	key info:
	time period: October 2023 to August 2024
	MT user ID: 6458976

	Area ID: 197786
*********************************/

-- Ensure #POSITIONS table exists
IF OBJECT_ID('tempdb..#POSITIONS') IS NOT NULL
    DROP TABLE #POSITIONS;

CREATE TABLE #POSITIONS (
    IMO INT,
    SHIP_ID INT,
    MMSI BIGINT,
    LAT REAL,
    LON REAL,
    SPEED_KNOTSX10 INT,
    HEADING INT,
    COURSE FLOAT,
    STATUS_AIS INT,
    TIMESTAMP_UTC DATETIME2(0),
    DRSC NVARCHAR(10),
    SHIPNAME NVARCHAR(100),
    SHIPTYPE NVARCHAR(50),
    GRT INT,
    LENGTH REAL,
    WIDTH REAL,
	DRAUGHT REAL,
    DWT INT
);

DECLARE @GeogCircle geography;
DECLARE @LAT_CENTER REAL = 28.44;
DECLARE @LON_CENTER REAL = 49.29;
DECLARE @RADIUS_KM REAL = 1.5;

-- Define the circular area as a geography object
SET @GeogCircle = geography::Point(@LAT_CENTER, @LON_CENTER, 4326).STBuffer(@RADIUS_KM * 1000); -- Convert km to meters

DECLARE @start_date DATETIME2(0) = '2023-10-01 00:00:00';
DECLARE @end_date DATETIME2(0) = '2024-08-31 23:59:59';

-- Define the bounding box to pre-filter records
DECLARE @LAT_MIN REAL = @LAT_CENTER - 0.0135;
DECLARE @LAT_MAX REAL = @LAT_CENTER + 0.0135;
DECLARE @LON_MIN REAL = @LON_CENTER - 0.0135;
DECLARE @LON_MAX REAL = @LON_CENTER + 0.0135;

DECLARE @db_name NVARCHAR(50);
DECLARE @sql NVARCHAR(MAX);

DECLARE db_cursor CURSOR FOR
SELECT name FROM sys.databases 
WHERE name IN ('AIS_ARCHIVE_2023B', 'AIS_ARCHIVE_2024A', 'AIS_ARCHIVE_2024B');

OPEN db_cursor;
FETCH NEXT FROM db_cursor INTO @db_name;

WHILE @@FETCH_STATUS = 0
BEGIN
    SET @sql = N'
    USE ' + QUOTENAME(@db_name) + N';

    WITH PositionCTE AS (
        SELECT
            S.IMO,
            PA.SHIP_ID,
            PA.MMSI,
            PA.LAT,
            PA.LON,
            PA.SPEED AS SPEED_KNOTSX10,
            PA.HEADING,
            PA.COURSE,
            PA.[STATUS] AS STATUS_AIS,
            PA.[TIMESTAMP] AS TIMESTAMP_UTC,
            (CASE 
                WHEN PA.STATION = 1000 THEN ''SAT'' 
                WHEN PA.STATION = 16600 THEN ''ROAM'' 
                ELSE ''TER'' 
            END) AS DRSC,
            S.SHIPNAME, 
            S.TYPE_NAME AS SHIPTYPE,
            S.GRT,
            S.LENGTH,
            S.WIDTH,
            (SELECT TOP 1 ES.NEW_DATA FROM AIS_EVENTS..EVENTS_SHIP ES WITH(NOLOCK) 
             WHERE ES.EVENT=14 AND ES.SHIP_ID = PA.SHIP_ID AND ES.TIMESTAMP <= PA.TIMESTAMP 
             ORDER BY ES.TIMESTAMP DESC) DRAUGHT,
            S.DWT
        FROM ' + @db_name + '.dbo.POS_ARCHIVE PA
        INNER JOIN ' + @db_name + '.dbo.SHIP S ON S.SHIP_ID = PA.SHIP_ID
        WHERE 
            -- Bounding Box Filter
            PA.LAT BETWEEN ' + CAST(@LAT_MIN AS NVARCHAR) + ' AND ' + CAST(@LAT_MAX AS NVARCHAR) + '
            AND PA.LON BETWEEN ' + CAST(@LON_MIN AS NVARCHAR) + ' AND ' + CAST(@LON_MAX AS NVARCHAR) + '

            -- Only relevant timestamps
            AND PA.[TIMESTAMP] BETWEEN '''+ CONVERT(NVARCHAR(50), @start_date, 120) + ''' 
                                   AND ''' + CONVERT(NVARCHAR(50), @end_date, 120) + '''

            -- Exclude invalid station codes
            AND PA.STATION > 0
            AND PA.STATION NOT IN (100, 200, 2000, 4000)
    )
    
    -- Final insert after circle filter
    INSERT INTO #POSITIONS (IMO, SHIP_ID, MMSI, LAT, LON, SPEED_KNOTSX10, HEADING, COURSE, STATUS_AIS, TIMESTAMP_UTC, 
                            DRSC, SHIPNAME, SHIPTYPE, GRT, LENGTH, WIDTH, DRAUGHT, DWT)
    SELECT IMO, SHIP_ID, MMSI, LAT, LON, SPEED_KNOTSX10, HEADING, COURSE, STATUS_AIS, TIMESTAMP_UTC, 
           DRSC, SHIPNAME, SHIPTYPE, GRT, LENGTH, WIDTH, DRAUGHT, DWT
    FROM PositionCTE
    WHERE geography::Point(LAT, LON, 4326).STIntersects(@GeogCircle) = 1;';

    -- Execute the query with parameterized geography object
    EXEC sp_executesql @sql, N'@GeogCircle geography', @GeogCircle;

    FETCH NEXT FROM db_cursor INTO @db_name;
END;

CLOSE db_cursor;
DEALLOCATE db_cursor;

-- Query positions and counts
SELECT * FROM #POSITIONS ORDER BY SHIP_ID, TIMESTAMP_UTC;
SELECT DRSC, COUNT(*) AS PositionCount FROM #POSITIONS GROUP BY DRSC;
SELECT COUNT(DISTINCT SHIP_ID) AS UniqueVesselCount FROM #POSITIONS;

-- Clean up temporary tables if needed
-- DROP TABLE IF EXISTS #POSITIONS;