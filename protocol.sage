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
import time
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

@dto.dataclass
class Count:
	n: int = 0
	
	def __call__(self):
		self.n += 1

bob_count = Count()
alice_count = Count()
transmission_count = Count()


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

@functools.lru_cache
def get_gauss(n: int):
	return DisGauss(ZpxQ, DEGREE, sigma=sqrt(n / 2))

def r_small(n):
	''' 
		The purpose of this function is to change easily the 
		type of random that the protocol uses.
	'''
	if n > 30:
		return get_gauss(n)()
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
class SetUpData:
	b:  'ZpxQ'
	a:  'matrix'
	A:  'matrix'
	C:  'matrix'
	expected_message: 'matrix'
	mask: list[int]
	e2: 'ZpxQ'
	r2: 'ZpxQ'

	@functools.cached_property
	def expected(self):
		return apply_mask(collapse(self.expected_message), self.mask) 

	def compute_c(self, s):
		return self.A * self.a + self.C * s


def _bob_set_up(s_param,  e2_param):
	n_elems = 2
	n_cols = 2 
	n_matrix = 3
	bob_count.n += n_elems + n_cols * M + n_matrix * (N * M)
	b = random_element()
	a = r_small_col(s_param)
	A = random_matrix()
	C = random_matrix()
	expected_message = b * A * a
	mask = list_of_bits(expected_message)  # not counted
	e2 = r_small_col(e2_param).transpose()
	r2 = b * C + e2
	return SetUpData(b, a, A, C, expected_message, mask, e2, r2)

@dto.dataclass 
class ProtocolData:
	s:  'matrix'
	c:  'ZpxQ'
	e1: 'ZpxQ'
	r1: 'ZpxQ'
	ab_product: 'ZpxQ'
	actual: 'matrix'

@dto.dataclass 
class CPlanData:
	set_up_data: SetUpData
	protocol_data: ProtocolData

	def check(self):
		return self.set_up_data.expected == self.protocol_data.actual

def _protocol(set_up_data, s_param, e1_param):
	alice_count()
	s = r_small_col(s_param)
	transmission_count()
	alice_matrix = 2
	alice_count.n += alice_matrix * (N * M)
	c = set_up_data.compute_c(s)
	bob_count.n += 2
	e1 = r_small(e1_param)
	transmission_count()
	r1 = set_up_data.b * c + e1
	alice_count()
	ab_product = r1 - set_up_data.r2 * s
	actual = apply_mask(collapse(ab_product), set_up_data.mask)
	return ProtocolData(s, c, e1, r1, ab_product, actual)


def protocol(s_param = 2, e1_param = 100_000, e2_param = 200):
	set_up_data = _bob_set_up(s_param, e2_param)
	protocol_data = _protocol(set_up_data, s_param, e1_param)
	data = CPlanData(set_up_data, protocol_data)
	return data.check()	

def protocol_collect_data(s_param = 2, e1_param = 100_000, e2_param = 200):
	set_up_data = _bob_set_up(s_param, e2_param)
	protocol_data = _protocol(set_up_data, s_param, e1_param)
	data = CPlanData(set_up_data, protocol_data)
	return None if data.check() else data
	
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


def _study_singular_time(_, s_param = 2, e1_param = 100_000, e2_param = 200):
	t0 = time.time()
	set_up_data = _bob_set_up(s_param, e2_param)
	t1 = time.time() 
	protocol_data = data = _protocol(set_up_data, s_param, e1_param)
	t2 = time.time() 
	return t1 - t0, t2 - t1

def study_time():
	with ProcessPoolExecutor() as executor:
			for t1, t2 in executor.map(_study_singular_time, range(10_000)):
				yield t1, t2
	

def write_study_time():
	with open('time.csv', 'w') as f:
		for t1, t2 in study_time():
			print(f'{t1}, {t2}', file=f)

# Test that homomorphic is working.
# test_homomorphic()
# Test is not needed, less bits is also efficient.
# assert protocol()  # messes with the count


import cProfile

if __name__ == "__main__":
	cProfile.run('protocol()')
	print('\n\n\n\n\n\n\n')
	print('Study of number of elements')
	print(f'Bob count {bob_count}')
	print(f'Alice count {alice_count}')
	print(f'Transmission count {transmission_count}')



