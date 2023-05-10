"""
Create relationship between ec2 type and cost for the prometheus advisor.
"""

def ec2_cost_calculator(ec2_type = "t2.micro"):
    """
    Function to calculate the cost of an ec2 type, on an hourly basis. 
    
    Parameters
    ---------
        ec2_type : 
        
    Returns
    -------
        queries: list[str]
        
    """
    
    