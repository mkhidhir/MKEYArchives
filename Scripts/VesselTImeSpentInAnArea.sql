/*********************************
    SAL-9279-Positions

    Prospect needs to see all vessels that passed this area in an easy-to-read format. 
    They did not specify any specific parameters, so it would be good to guide them by adding vessel type, size, and other relevant details.

    Please share the full extraction and a separate copy with limited rows as a sample. Also, provide an indication of the quantity of data.

    Key Info:
    Time period: October 2023 to August 2024
    MT user ID: 6458976
    Area ID: 197786
*********************************/
--FUNCTION AT THE BOTTOM

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
    VESSEL_NAME NVARCHAR(100),
    VESSEL_TYPE NVARCHAR(50),
    GRT INT,
    LENGTH REAL,
    WIDTH REAL,
    DRAUGHT REAL,
    DWT INT,
    ARRIVED_FROM NVARCHAR(100),
    ARRIVED_FROM_TIMESTAMP_UTC DATETIME2(0),
    DEPARTURE_TO NVARCHAR(100),
    DEPARTURE_TO_TIMESTAMP_UTC DATETIME2(0)
);

DECLARE @GeogCircle geography;
DECLARE @LAT_CENTER REAL = 28.447496;
DECLARE @LON_CENTER REAL = 49.299337;
DECLARE @RADIUS_KM REAL = 1.5;

SET @GeogCircle = geography::Point(@LAT_CENTER, @LON_CENTER, 4326).STBuffer(@RADIUS_KM * 1000);

DECLARE @start_date DATETIME2(0) = '2023-10-01 00:00:00';
DECLARE @end_date DATETIME2(0) = '2024-08-31 23:59:59';

DECLARE @LAT_MIN REAL = @LAT_CENTER - 0.0162;
DECLARE @LAT_MAX REAL = @LAT_CENTER + 0.0162;
DECLARE @LON_MIN REAL = @LON_CENTER - 0.0162;
DECLARE @LON_MAX REAL = @LON_CENTER + 0.0162;

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
            S.SHIPNAME AS VESSEL_NAME, 
            S.TYPE_NAME AS VESSEL_TYPE,
            S.GRT,
            S.LENGTH,
            S.WIDTH,
            (SELECT TOP 1 ES.NEW_DATA FROM AIS_EVENTS..EVENTS_SHIP ES WITH(NOLOCK) 
             WHERE ES.EVENT=14 AND ES.SHIP_ID = PA.SHIP_ID AND ES.TIMESTAMP <= PA.TIMESTAMP 
             ORDER BY ES.TIMESTAMP DESC) DRAUGHT,
            S.DWT,
            PREVIOUS_PORT.PORT_NAME AS ARRIVED_FROM,
			PREVIOUS_PORT.TIMESTAMP AS ARRIVED_FROM_TIMESTAMP_UTC,
            NEXT_PORT.PORT_NAME AS DEPARTURE_TO,
			NEXT_PORT.TIMESTAMP AS DEPARTURE_TO_TIMESTAMP_UTC
        FROM ' + @db_name + '.dbo.POS_ARCHIVE PA
        INNER JOIN ' + @db_name + '.dbo.SHIP S ON S.SHIP_ID = PA.SHIP_ID
        OUTER APPLY (
            SELECT TOP 1 P1.PORT_NAME, PM1.TIMESTAMP 
            FROM AIS..PORT_MOVES PM1
            INNER JOIN AIS..PORTS P1 ON PM1.PORT_ID = P1.PORT_ID
            WHERE PM1.SHIP_ID = PA.SHIP_ID 
            AND PM1.TIMESTAMP < PA.[TIMESTAMP]
            AND PM1.INTRANSIT = 0
            AND PM1.MOVE_TYPE = 1
			AND PM1.PORT_TYPE = ''P''
            ORDER BY PM1.TIMESTAMP DESC
        ) AS PREVIOUS_PORT
        OUTER APPLY (
            SELECT TOP 1 P2.PORT_NAME, PM2.TIMESTAMP
            FROM AIS..PORT_MOVES PM2
            INNER JOIN AIS..PORTS P2 ON PM2.PORT_ID = P2.PORT_ID
            WHERE PM2.SHIP_ID = PA.SHIP_ID 
            AND PM2.TIMESTAMP > PA.[TIMESTAMP]
            AND PM2.INTRANSIT = 0
            AND PM2.MOVE_TYPE = 0
			AND PM2.PORT_TYPE = ''P''
            ORDER BY PM2.TIMESTAMP
        ) AS NEXT_PORT
        WHERE 
            PA.LAT BETWEEN ' + CAST(@LAT_MIN AS NVARCHAR) + ' AND ' + CAST(@LAT_MAX AS NVARCHAR) + '
            AND PA.LON BETWEEN ' + CAST(@LON_MIN AS NVARCHAR) + ' AND ' + CAST(@LON_MAX AS NVARCHAR) + '
            AND PA.[TIMESTAMP] BETWEEN '''+ CONVERT(NVARCHAR(50), @start_date, 120) + ''' 
                                       AND ''' + CONVERT(NVARCHAR(50), @end_date, 120) + '''
            AND PA.STATION > 0
            AND PA.STATION NOT IN (100, 200, 2000, 4000)
    )
    
    INSERT INTO #POSITIONS 
    SELECT * FROM PositionCTE
    WHERE geography::Point(LAT, LON, 4326).STIntersects(@GeogCircle) = 1;';

    EXEC sp_executesql @sql, N'@GeogCircle geography', @GeogCircle;

    FETCH NEXT FROM db_cursor INTO @db_name;
END;

CLOSE db_cursor;
DEALLOCATE db_cursor;

/*WHERE THE FUNCTION OF THE SCRIPT SAYS*/
WITH PositionWithLag AS (
    SELECT 
        SHIP_ID,
        IMO,
        MMSI,
		VESSEL_NAME,
        TIMESTAMP_UTC,
        LAG(TIMESTAMP_UTC) OVER (PARTITION BY SHIP_ID ORDER BY TIMESTAMP_UTC) AS PREV_TIMESTAMP
    FROM #POSITIONS
),
EntryExitFlags AS (
    SELECT 
        SHIP_ID,
        IMO,
        MMSI,
		VESSEL_NAME,
        TIMESTAMP_UTC,
        CASE 
            WHEN PREV_TIMESTAMP IS NULL OR DATEDIFF(MINUTE, PREV_TIMESTAMP, TIMESTAMP_UTC) > 60 
            THEN 1 ELSE 0 
        END AS IS_NEW_SESSION
    FROM PositionWithLag
),
SessionNumbering AS (
    SELECT 
        SHIP_ID,
        IMO,
        MMSI,
		VESSEL_NAME,
        TIMESTAMP_UTC,
        SUM(IS_NEW_SESSION) OVER (PARTITION BY SHIP_ID ORDER BY TIMESTAMP_UTC ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS SESSION_ID
    FROM EntryExitFlags
),
SessionDurations AS (
    SELECT 
        SHIP_ID,
        IMO,
        MMSI,
		VESSEL_NAME,
        SESSION_ID,
        MIN(TIMESTAMP_UTC) AS ENTRY_TIME, 
        MAX(TIMESTAMP_UTC) AS EXIT_TIME,
        DATEDIFF(MINUTE, MIN(TIMESTAMP_UTC), MAX(TIMESTAMP_UTC)) AS TIME_SPENT_MINUTES
    FROM SessionNumbering
    GROUP BY SHIP_ID, IMO, MMSI, VESSEL_NAME, SESSION_ID
)

SELECT 
    SHIP_ID,
    IMO,
    MMSI,
	VESSEL_NAME,
    SUM(DATEDIFF(MINUTE, ENTRY_TIME, EXIT_TIME)) AS TOTAL_MINUTES,
    FORMAT(SUM(DATEDIFF(MINUTE, ENTRY_TIME, EXIT_TIME)) / 1440, '0') + 'd ' +
    FORMAT((SUM(DATEDIFF(MINUTE, ENTRY_TIME, EXIT_TIME)) % 1440) / 60, '0') + 'h ' +
    FORMAT(SUM(DATEDIFF(MINUTE, ENTRY_TIME, EXIT_TIME)) % 60, '0') + 'm' AS TOTAL_TIME_SPENT
FROM SessionDurations
GROUP BY SHIP_ID, IMO, MMSI, VESSEL_NAME
ORDER BY TOTAL_MINUTES DESC;
/*WHERE THE FUNCTION OF THE SCRIPT SAYS*/

SELECT TOP 100 * FROM #POSITIONS ORDER BY TIMESTAMP_UTC;
SELECT DRSC, COUNT(*) AS PositionCount FROM #POSITIONS GROUP BY DRSC;
SELECT COUNT(DISTINCT SHIP_ID) AS UniqueVesselCount FROM #POSITIONS;