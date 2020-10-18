from functions.basics.aio_mysql_excute import execute_sql


async def get_total_calls(data_name: str) -> int:
    """
    Get function calls total count

    Args:
        data_name: Data to query
            data name list:
                setuCalled: Number of setu calls
                realCalled: Number of real calls
                bizhiCalled: Number of bizhi calls
                weatherCalled: Number of weather query calls
                responseCalled: Number of total calls
                clockCalled: Number of get time calls
                searchCount: Number of search img calls
                botSetuCount: Number of listen bot img calls
                dialsCount: Number of clock dials
                predictCount: Number of predict img calls
                yellowPredictCount: Number of yellow predict img calls
                quotesCount: Number of get quotes calls

    Examples:
        data = await get_total_calls("setuCalled")

    Return:
        int
    """
    sql = "SELECT %s from calledCount" % data_name
    data = await execute_sql(sql)
    return data[0][0]
