# import src.ooni.utils as ooni_utils

class Alpha2 ():
    '''
    Represents an ISO alpha-2 country code.
    '''
    def __init__(self,
                 country_code: str):
        assert(ooni_utils.is_nonempty_str(country_code))
        assert(len(country_code)==2)
        self.country_code = country_code

    def __str__(self):
        return f'{self.country_code}'

    def __repr__(self):
        return self.__str__()
