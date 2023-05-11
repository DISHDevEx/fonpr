"""
Create relationship between ec2 type and cost for the prometheus advisor.
"""

def ec2_cost_calculator(ec2_type = "t2.micro"):
    """
    Function to calculate the cost of an EC2 type, on an hourly basis. 
    
    Parameters
    ---------
        ec2_type : String
            String that indicates the type of EC2 that cost should be calculated for. 
        
    Returns
    -------
        hourly_cost: Int
            Integer value that represents the dollar amount for the cost of the specified ec2 type.
        
    """
    
    pricing_table = {
        "t2.micro": 0.0116,
        "m4.large": 0.10,
        "t3.medium": 0.0416,
    }
    
    
    if ec2_type not in pricing_table:
        raise Exception("sorry ec2 type not defined in pricing table")
    
    cost = pricing_table[ec2_type]
    return cost

    