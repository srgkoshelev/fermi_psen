from wand.image import Image
import fnmatch
import re
import os
import heat_transfer as ht
from math import pi, log
ureg = ht.ureg
u = ureg
Q_ = ht.Q_


def make_pics(fname):
    """Create pictures of a PDF file with a given name"""
    try:
        pics = sorted(fnmatch.filter(os.listdir('images'), f'{fname}*.png'))
    except FileNotFoundError as e:
        print(missing_file_error(e, fname))
        return None
    if not pics:
        try:
            with Image(filename=f'images/{fname}.pdf', resolution=200) as img:
                with img.convert('png') as converted:
                    converted.save(filename=f'images/{fname}_page.png')
        except Exception as e:
            print(missing_file_error(e, fname))
    for pic_fn in pics:
        print(r'#+ATTR_LATEX: :width \textwidth')
        print(f'[[./images/{pic_fn}]]')
    return None


def missing_file_error(error, fname):
    """Formats into Latex an error message for missing file."""
    message = str(error)
    if fname in message:
        err_message = r'\colorbox{red}{' + \
            f'Missing {fname} file'.replace("_", " ") + '}'
        return err_message
    elif 'images' in message:
        err_message = r'\colorbox{red}{' + \
            f'Missing "images" folder when processing {fname} file'.replace(
                "_", " ") + '}'
        return err_message
    else:
        return error


class Component:
    def __init__(self, name, size, source, P):
        self.name = name
        self.size = size
        self.source = source
        self.P = P


class Material():
    """Basic material class."""
    def __init__(self, name):
        self.name = name  # will be used in property calculations

        def kappa(self, T1, T2=None):
            """Calculate temperature conductivity at a given temperature."""
            return ht.nist_property(self.name, 'TC', T1, T2)

        def lin_exp(self, T):
            """Calculate linear expansion for given temperature"""
            try:
                return ht.nist_property(self.name, 'LE', T)
            except KeyError:
                return ht.nist_property(self.name, 'EC', 293*u.K, T) * \
                    (T-293*u.K)


SS304 = Material('304SS')
SS304.rho = Q_('7859 kg/m**3')
SS304.S = Q_('16700 psi')  # 304L SS allowable stress
SS304.nu = 0.3  # Poisson's ratio
SS304.T_min = Q_(-425, u.degF)

copper = Material('copper')
copper.S = Q_('6000 psi')
copper.T_min = Q_(-452, u.degF)
