from logging_config import LogRoute

class FilterHelpers():
    # Method to determine if an id property is in the requested filters and should be added.
    @classmethod
    def add_id_filter(cls, query_filters, filters, filter_to_apply, id_to_filter):
        if filter_to_apply in filters:
            LogRoute.verbose(f"Item '{filter_to_apply}' of {filters[filter_to_apply]} in filters.")
            query_filters.append(id_to_filter == int(filters[filter_to_apply]))
        return query_filters

    # Method to determine if an item property is in the requested filters and should be added.
    @classmethod
    def add_is_equal_to_filter(cls, query_filters, filters, filter_to_apply, property_to_filter):
        if filter_to_apply in filters:
            LogRoute.verbose(f"Item '{filter_to_apply}' of {filters[filter_to_apply]} in filters.")
            query_filters.append(property_to_filter == filters[filter_to_apply])
        return query_filters

    # Method to determine if there are an upper and/or bound to a property is in the requested filters and should be added.
    @classmethod
    def add_bound_to_filter(cls, query_filters, filters, filter_to_apply, property_to_filter):
        query_filters = cls.add_is_equal_to_filter(query_filters, filters, filter_to_apply, property_to_filter)

        # Only check for a bound if the request doesn't have a specific requested value
        if filter_to_apply not in filters:
            lower_bound = filters.get(filter_to_apply + "_min")
            upper_bound = filters.get(filter_to_apply + "_max")

            # If both bounds exist yet are invalid (i.e., the upper bound is less than the lower bound) then do not apply.
            if lower_bound and upper_bound and (lower_bound > upper_bound):
                return query_filters

            if lower_bound:
                LogRoute.verbose(f"Item '{filter_to_apply}' >= {lower_bound} in filters.")
                query_filters.append(property_to_filter >= lower_bound)

            if upper_bound:
                LogRoute.verbose(f"Item '{filter_to_apply}' <= {upper_bound} in filters.")
                query_filters.append(property_to_filter <= upper_bound)

        return query_filters
