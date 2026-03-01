class Vector3:
     _epsilon:float = 1e-6 # class variable to show the smallest unit after which we consider it to be zero

     def __init__(self, x:float, y:float, z:float = 0.0):
         """
         Vector3 is a dtype which helps in calculation of object's state
         
         :param self:
         :param x: Description

         :type x: float
         :param y: Description
         
         :type y: float
         :param z: Description
         
         :type z: float
         """   
         self._x:float = x
         self._y:float = y
         self._z:float = z

     @property
     def x(self) -> float:
         return self._x
     
     @property
     def y(self):
         return self._y

     @property
     def z(self):
         return self._z

     
     @property
     def length(self):
         return self.__abs__()
     
     @property
     def length_squared(self):
         return self.x**2 + self.y**2 + self.z**2

     def __add__(self, other):
         if isinstance(other, Vector3):
             return Vector3(self.x + other.x, self.y + other.y, self.z + other.z)
         raise TypeError('Expected Vector3')

     def __radd__(self, other):
         return self.__add__(other)

     def __sub__(self, other):
         if isinstance(other, Vector3):
             return Vector3(self.x - other.x, self.y - other.y, self.z - other.z)
         raise TypeError('Expected Vector3')     

     def __rsub__(self, other):
         return Vector3(other.x - self.x, other.y - self.y, other.z - self.z)
     
     def __mul__(self, other):
         if isinstance(other, (int, float)):
             return Vector3(self.x * other, self.y * other, self.z * other)
         raise TypeError('Expected int or float value for scalar. use .dot() method to multiply two vectors')

     def __rmul__(self, other):
         return self.__mul__(other)
     
     def __truediv__(self,other):
         if other == 0:
             raise ZeroDivisionError
         
         if isinstance(other, (int,float)):
             return Vector3(self.x/other, self.y/other, self.z/other)
         raise TypeError('Expected int or float value for scalar')
     
     def __abs__(self):
         return self.length_squared ** 0.5
     
     def __neg__(self):
         return Vector3(0-self.x, 0-self.y, 0-self.z)

     def dot(self, other):
         if isinstance(other, Vector3):
             return self.x * other.x + self.y * other.y + self.z * other.z
         raise TypeError('Expected Vector3')
     
     def cross(self, other):
         """Compute the cross product of two Vector3s"""
         if isinstance(other, Vector3):
             return Vector3(
                 self.y * other.z - self.z * other.y,
                 self.z * other.x - self.x * other.z,
                 self.x * other.y - self.y * other.x
             )
         raise TypeError('Expected Vector3')
     
     def normalized(self):
         mag = self.__abs__()
         if mag > self._epsilon:
             return self.__truediv__(self.__abs__())
         else:
             return Vector3(0, 0, 0)
     
     def is_close(self, other):
         if isinstance(other, Vector3):
             return True if abs(self.x - other.x) <= self._epsilon and abs(self.y - other.y) <= self._epsilon and abs(self.z - other.z) <= self._epsilon else False
         
         raise TypeError('Expected Vector3')
     
     def __repr__(self) -> str:
         return f'({self.x},{self.y},{self.z})'
