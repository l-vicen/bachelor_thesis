from pyomo.environ import *
from pao.pyomo import *

# Upper-level definition: Auction Problem
model = ConcreteModel("Upper-level: Auction Problem")

'''   Model Subscripts

model.i := Set of auctioned items.
model.j := Set of auction participating suppliers.

'''
model.i = Set(initialize=['Apples', 'Bananas', 'Tomatos'], doc='Auctioned Items')
model.j = Set(initialize=['Christina_GmbH', 'Lucas_GmbH'], doc='Auction Participating Suppliers')

''' Upper-level decision variable 

model.X := Binary variable, equal to 1 if quotation for item i is allocated to supplier j ; 0
otherwise.

'''
model.X = Var(model.j, model.i, domain=Binary, doc='Decision Variable X') 

# Lower-level definition: Pricing Problem 
model.L = SubModel(fixed=model.X)

''' Lower-level decision variable 

model.L.P := Real variable, represents the supplier bid price.

'''
model.L.P = Var(model.j, model.i, domain=Reals, doc='Decision Variable P') 

''' Model Parameters 

model.Demand := the total demand for item i submitted by auctioneer.
model.Utility := expected utility from purchase by the auctioneer.
model.supply_capacity := the quantity of item i that supplier j can procure.
model.production_costs := the production cost of item i if produced by supplier j.

'''
supplier_capacity = {
    ('Christina_GmbH', 'Apples'): 15,
    ('Lucas_GmbH', 'Apples'): 15,
    ('Christina_GmbH', 'Bananas'): 25,
    ('Lucas_GmbH', 'Bananas'): 15,
    ('Christina_GmbH', 'Tomatos'):40,
    ('Lucas_GmbH', 'Tomatos'): 50,
}

production_costs = {
    ('Christina_GmbH', 'Apples'): 9.75,
    ('Lucas_GmbH', 'Apples'): 7.5,
    ('Christina_GmbH', 'Bananas'): 12.5,
    ('Lucas_GmbH', 'Bananas'): 15,
    ('Christina_GmbH', 'Tomatos'): 37.5,
    ('Lucas_GmbH', 'Tomatos'): 50,
}

model.Demand = Param(model.i, initialize={'Apples':15, 'Bananas':25, 'Tomatos':50}, doc='Budget Items')
model.Utility = Param(model.i, initialize={'Apples':20, 'Bananas':30, 'Tomatos':50}, doc='Expected Utility')
model.supply_capacity = Param(model.j, model.i, initialize=supplier_capacity, doc='Supply Capacity of Suppliers')

model.L.Budget = Param(model.i, initialize={'Apples':10, 'Bananas':20, 'Tomatos':50}, doc='Demand Items')
model.L.production_costs = Param(model.j, model.i, initialize=production_costs, doc='Production Cost per Supplier')


''' Model Objective Functions

1) Upper-level: 

    def auction_objective_function(model)  := Maximizes the return of expected utility for given item purchase (Utility * X - Supplier Price)

2) Lower-level:

    def pricing_objective_function(model)  := Maximizes the overall bid price submission.

'''
def auction_objective_function(model):
    return sum((model.Utility[i] * model.X[j,i]) - model.L.P[j,i] for j,i in model.j*model.i)

def pricing_objective_function(submodel, model):
    return sum(submodel.P[j,i] for j,i in model.j * model.i)

# Objective function assignments
model.o = Objective(rule=auction_objective_function(model), sense=maximize, doc='Auction Problem') # Upper-level 
model.L.o = Objective(rule= pricing_objective_function(model.L, model), sense=maximize, doc='Pricing Problem') # Lower-level

''' Model Constraints

1) Upper-level: 

    def single_sourcing_constraint(model, i): Ensures there is only 1 winner per auctioned item.

    def demand_requirement_constraint(model, i): Ensures that the respective supplier can supply the whole quantity of the demanded item. 

2) Lower-level:

    def lower_and_upper_bound_constraint(submodel, j, i): Ensures that the submitted bid prices lays within a reasonable range. 
    The lower bound represents the cost of production, the upper bound represents the auctioneer budget.

'''
def single_sourcing_constraint(model, i):
    return sum(model.X[j,i] for j in model.j) == 1

def demand_requirement_constraint(model, i):
    return sum(model.supply_capacity[j,i] * model.X[j,i] for j in model.j) == model.Demand[i]

# Upper-level constraint assignments
model.SingleSourcingConstraint = Constraint(model.i, rule=single_sourcing_constraint, doc='There is at most 1 winner')
model.DemandConstraint = Constraint(model.i, rule=demand_requirement_constraint, doc='Auctioneer demand is fulfilled')

def lower_and_upper_bound_constraint(submodel, j, i):
    return (submodel.production_costs[j,i], submodel.P[j,i], submodel.Budget[i])

# Lower-level constraint assignment
model.L.DemandConstraint = Constraint(model.j, model.i, rule=lower_and_upper_bound_constraint, doc='Bid Price is non-negative')

# Visualizing model composition
# model.pprint()

# Calling the Big-M Relaxation Solver
solver = Solver('pao.pyomo.FA')
solver.solve(model)

# Visualizing model composition with results
model.pprint()

# model.display()
# solver.write()
# solver.pptrint()