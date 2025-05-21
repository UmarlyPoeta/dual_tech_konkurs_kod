import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

# siatka kątów i wysokości
theta = np.linspace(0, 2*np.pi, 100)
z = np.linspace(-5, 5, 100)
theta, z = np.meshgrid(theta, z)

# promień i środek
r = 2
x0 = 2

# współrzędne walca
x = x0 + r * np.cos(theta)
y = r * np.sin(theta)

# rysunek 3D
fig = plt.figure()
ax = fig.add_subplot(111, projection='3d')
ax.plot_surface(x, y, z, alpha=0.7, color='skyblue')

# ustawienia osi
ax.set_xlabel('X')
ax.set_ylabel('Y')
ax.set_zlabel('Z')
ax.set_title('Walec: (x - 2)^2 + y^2 ≤ 4')

plt.show()
