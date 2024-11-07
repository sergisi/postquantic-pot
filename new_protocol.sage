'''
Module that has the protocol described on the article 
	`Quantum-resistant asymmetric blind computation with 
	applications to priced oblivious transfer`
  

The protocol is described as the function protocol(), and 
has some helper functions, mainly to derive stats from 
the protocol or some security.

It has some helper functions to collect more than one execution, 
skimming all the times that the protocol has been correct.
'''
import numpy as np
from concurrent.futures import ProcessPoolExecutor
import dataclasses as dto
import math
import itertools 
import functools
from sage.stats.distributions.discrete_gaussian_polynomial import DiscreteGaussianDistributionPolynomialSampler as DisGauss
import random

LEN_BITS = 8
p= 12 * 1024 + 1
LEN_BITS = math.ceil(math.log2(p))
DEGREE = 1024
N = 1
M = 2
SMALL_DEGREE = DEGREE
SMALL_MAX_VALUE = 2
CBD = 2


Zp=Integers(p)
Zpx.<x> = Zp[]
ZpxQ = Zpx.quotient(x**DEGREE + 1, 'X')
rand_gauss = DisGauss(ZpxQ, DEGREE, sigma=2.87)

def cbd(n: int = CBD):
	return random.binomialvariate(n, 0.5) \
		- random.binomialvariate(n, 0.5)


def random_element():
	result = DEGREE*[0]
	for j in range(DEGREE):
		result[j] = Zp(randint(0,p-1))
	return(ZpxQ(result))

def random_matrix(size_n=N, size_m=M):
	m = matrix(ZpxQ, size_n, size_m)
	for i in range(size_n):
		for j in range(size_m):
			m[i,j] = random_element()
	return m

def random_vector_row(size=N):
	m = matrix(ZpxQ,1,size)
	for i in range(size):
		m[0,i] = random_element()
	return(m)

def random_vector_column(size=N):
	m = matrix(ZpxQ,size,1)
	for i in range(size):
		m[i,0] = random_element()
	return(m)

##########################

def random_element_small(
		grau_small=SMALL_DEGREE,
		rand_function = lambda: Zp(randint(-SMALL_MAX_VALUE,SMALL_MAX_VALUE-1))
	):
	result = (grau_small+1)*[0]
	for j in range(grau_small+1):
		result[j] = rand_function()
	return(ZpxQ(result))

def random_vector_row_small(size=N, 
							 rand_element = lambda: random_element_small(SMALL_DEGREE)):
	m = matrix(ZpxQ,1,size)
	for i in range(size):
		m[0,i] = rand_element()
	return(m)

def random_vector_column_small(size=N, rand_element = lambda: random_element_small()):
	m = matrix(ZpxQ,size,1)
	for i in range(size):
		m[i,0] = rand_element()
	return(m)

def r_small(n):
	''' 
		The purpose of this function is to change easily the 
		type of random that the protocol uses.
	'''
	return random_element_small(rand_function=lambda: cbd(n))

def r_small_col(n): 
	return random_vector_column_small(size=M, 
									rand_element=lambda: r_small(n))

def check_one_noise():
	s = r_small_col(2)
	e1 = r_small(100_000)
	e2 = r_small_col(100)
	v = e1 - e2.transpose() * s
	return max(abs(x) for x in collapse_to_list(v))


def collapse(v):
	try :
		w = v[0][0]
		v = w
	except:
		pass
	q2 = p // 2
	v1 = (int(coef) % p for coef in v)
	v2 = (coef if coef < q2 else p - coef for coef in v1)
	q4 = q2 // 2
	v3 = (0 if coef < q4 else 1 for coef in v2)
	return tuple(v3)

def collapse_to_list(v):
	try :
		w = v[0][0]
		v = w
	except:
		pass
	q2 = p // 2
	v1 = (int(coef) % p for coef in v)
	return list(coef if coef < q2 else coef - p for coef in v1)

##########################
def to_numpy(f: 'vector') -> 'np.array':
	return np.array(
		[
			np.array(list(x), dtype=np.int_) 
			for x in f.coefficients()
		]
	)
	
def list_of_bits(coefs):
	v = coefs[0][0]
	q2 = p // 2
	v1 = (int(coef) % p for coef in v)  
	v2 = (coef if coef < q2 else p - coef for coef in v1)
	q4 = q2 // 2
	v3 = (abs(coef - q4) for coef in v2)
	v4 = ((c, i) for i, c in enumerate(v3))
	v5 = list(filter(lambda x: x[0] > 2000, v4))
	res = random.sample(v5, k=256)
	res = [i for _, i in res]
	res = sorted(res)
	return res
	

def apply_mask(ls, mask):
	return [ls[i] for i in mask]


@dto.dataclass 
class CPlanData:
	b:  'ZpxQ'
	a:  'matrix'
	A:  'matrix'
	s:  'matrix'
	C:  'matrix'
	c:  'ZpxQ'
	e1: 'ZpxQ'
	e2: 'ZpxQ'
	r1: 'ZpxQ'
	r2: 'ZpxQ'
	ab_product: 'ZpxQ'
	mask: list[int]
	expected_message: 'matrix'
	expected: 'matrix'
	actual: 'matrix'

def _protocol(s_param = 2, e1_param = 100_000, e2_param = 200):
	b = random_element()
	a = r_small_col(s_param)
	A = random_matrix()
	s = r_small_col(s_param)
	C = random_matrix()
	expected_message = b * A * a
	mask = list_of_bits(expected_message)
	expected = apply_mask(collapse(expected_message), mask)
	c = A * a + C * s
	e1 = r_small(e1_param)
	e2 = r_small_col(e2_param).transpose()
	r1 = b*c + e1
	r2 = b*C + e2
	ab_product = r1 - r2 * s
	actual = apply_mask(collapse(ab_product), mask)
	return CPlanData(b, a, A, s, C, c, e1, e2, r1, r2, ab_product, mask, expected_message, expected, actual)


def protocol():
	data = _protocol()
	return 0 if data.actual == data.expected else 1
	

def protocol_collect_data():
	data = _protocol(2, 100_000, 100)
	return None if data.actual == data.expected else data
	
def check_some(_):
	res = []
	for e in (protocol_collect_data() for _ in range(1000)):
		if e is not None:
			res.append(e)
	return res

def collect_data():
	with ProcessPoolExecutor(max_workers=8) as executor:
		ls = executor.map(check_some, range(8))
		return list(itertools.chain(*ls))


if __name__ == "__main__":
    print(protocol())
