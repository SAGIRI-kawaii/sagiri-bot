class ImageMessageCache:
    __instance = None
    __first_init = False
    __cache_dict = {}

    def __new__(cls):
        if not cls.__instance:
            cls.__instance = object.__new__(cls)
        return cls.__instance

    def __init__(self):
        if not self.__first_init:
            ImageMessageCache.__first_init = True

    @classmethod
    def get_instance(cls):
        if cls.__instance:
            return cls.__instance
        else:
            raise ValueError("ImageMessageCacheNotInitialized")

    def upload(self, message_id: int, path: str):
        if message_id in self.__cache_dict.keys():
            pass
        else:
            if len(self.__cache_dict.keys()) > 1000:
                self.__cache_dict.pop(0)
            self.__cache_dict[message_id] = path

    def get_image_path(self, message_id: int):
        if message_id in self.__cache_dict.keys():
            return self.__cache_dict[message_id]
        else:
            return None