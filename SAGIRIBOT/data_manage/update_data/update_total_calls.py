from SAGIRIBOT.basics.aio_mysql_excute import execute_sql


async def update_total_calls(new_data: int, operation_type: str) -> None:
    """
    Update function calls total count

    Args:
        operation_type: Data to modify
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
        new_data: New value of data to modify

    Examples:
        data = await update_total_calls(300, "setuCalled")

    Return:
        None
    """
    operation = {
        "setu": "setuCalled",
        "real": "realCalled",
        "bizhi": "bizhiCalled",
        "weather": "weatherCalled",
        "response": "responseCalled",
        "clock": "clockCalled",
        "search": "searchCount",
        "botSetuCount": "botSetuCount",
        "predict": "predictCount",
        "yellow": "yellowPredictCount",
        "quotes": "quotesCount"
    }
    if operation_type in operation.keys():
        sql = "UPDATE calledCount SET %s=%d" % (operation[operation_type], new_data)
        await execute_sql(sql)
    else:
        raise Exception("error: none operationType named %s!" % operation_type)
