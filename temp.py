import pandas as pd
from datetime import datetime
import matplotlib.pyplot as plt

data = {
    'state':['Ohio','Ohio','Ohio','Nevada','Nevada'],
    'year':[2000,2001,2002,2001,2002],
    'pop':[1.5,1.7,3.6,2.4,2.9]
}
frame = pd.DataFrame(data)
y = frame['pop']
x= frame['state']
plt.plot(y,x)
plt.show()