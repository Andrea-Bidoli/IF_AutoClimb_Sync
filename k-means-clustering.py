import numpy as np
from sklearn.cluster import KMeans
import matplotlib.pyplot as plt

# Sample data
ratios = [0.03055121218804333, 0.017110131866719946, 0.0007236275369983054, 0.016962396665206186,
          0.003823645554913613, 0.019077139516520746, 0.02547725432890253, 0.03055121218804333]

ratios1 = [0.04889815194620194, 0.033665919485527836, 0.0321207466974499, 0.02250652458486452,
    0.02074444271000046, 0.0170816281020401, 0.007517086948037762, 0.012267311950948679,
    0.0014996970918580033, 0.00040924103730039635, 0.0037012707896833283, 0.004246997581941336,
    0.0002556539874857392, 0.002171215444543572, 0.0009798184720574681, 0.025337521122291626,
    0.008820528282212541, 0.03478332515326191, 0.011089406569535918, 0.017305600118666685,
    0.021855423330495883, 0.02459551768949858, 0.01562137134083138, 0.02137021167692938,
    0.022491549897194665, 0.019447098289718707, 0.021369236096106862, 0.01828271405584148,
    0.014711265981333446, 0.04889815194620194]

# Convert to numpy array and reshape for clustering
ratios = np.array(ratios).reshape(-1, 1)

# Apply K-means clustering
kmeans = KMeans(n_clusters=2, random_state=0).fit(ratios)
labels = kmeans.labels_
centers = kmeans.cluster_centers_

print("Cluster Centers:", centers)

# Visualize the clusters
plt.scatter(range(len(ratios)), ratios, c=labels, cmap='viridis')
plt.axhline(y=centers[0], color='r', linestyle='--', label=f'Center 0: {centers[0][0]:.2f}')
plt.axhline(y=centers[1], color='b', linestyle='--', label=f'Center 1: {centers[1][0]:.2f}')
plt.xlabel('Data Point Index')
plt.ylabel('Altitude/Distance Ratio')
plt.legend()
plt.show()

# Determine threshold
threshold = np.mean(centers)
print(f"Determined Threshold: {threshold:.4f}")
