def retrieve_output_from_endpoint(result, key):
    success_check = (result[1] == 200)
    output = result[0].get_json()
    if success_check:
        output_value = output[key]
        if not isinstance(output_value, dict):
            return output_value, success_check
        return output_value.get("output", output_value), success_check
    else:
        return output, success_check