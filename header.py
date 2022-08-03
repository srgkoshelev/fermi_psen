from wand.image import Image
import fnmatch
import re
import os
import heat_transfer as ht
from math import pi, log
from dataclasses import dataclass
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


def format_err_msg(txt):
    """Format error message for high visibility in Latex export."""
    start = r'\colorbox{red}{'
    main = txt.replace("_", " ")
    end = '}'
    return start + main + end

def missing_file_error(error, fname):
    """Formats into Latex an error message for missing file."""
    message = str(error)
    if fname in message:
        err_message = format_err_msg(f'Missing {fname} file')
        return err_message
    elif 'images' in message:
        err_message = format_err_msg(
            f'Missing "images" folder when processing {fname} file')
        return err_message
    else:
        return error


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


@dataclass
class Component:
    name: str
    size: str
    source: str
    P: u.Quantity
    material: Material
    type: str = 'Fitting'


def get_materials(*elements):
    materials = set()
    for element in elements:
        materials.add((element.type, element.material))
    return materials


def summarize_material(materials):
    material_names = set()
    for material in materials:
        material_names.add(material[1].name)
    if len(material_names) == 1:
        return list(material_names)[0]
    elif all([re.search('^3.*SS$', name) for name in material_names]):
        return '300 series stainless steel'
    else:
        return format_err_msg('Different materials used, correct manually')


def check_low_stress(P_des, T_des, components, *, E, W, Y):
    """Check whether the piping system satisfies low stress piping requirements
    as defined by FESHM 5031.1"""
    if P_des >= Q_(150, u.psid):
        print('Pressure too high for low stress category.')
        return False
    if any([(P_des/pressure_rating(c, E, W, Y)) > 0.2 for c in components]):
        print('Stress ratio too high for low stress category.')
        return False
    if T_des > Q_(366, u.degC):
        print('Design temperature too high for low stress category.')
        return False
    if any([T_des < c.material.T_min for c in components]):
        print('Material is not listed for this temperature.')
        return False
    else:
        return True


def pressure_rating(component, E, W, Y):
    if component.type == 'Tube':
        rating = ht.piping.pressure_rating(component,
                                           S=component.material.S,
                                           E=E, W=W, Y=Y)
    elif component.type == 'Fitting':
        rating = component.P
    else:
        raise TypeError('Unknown component type: {component.type}')
    return rating




SS304 = Material('304SS')
SS304.rho = Q_('7859 kg/m**3')
SS304.S = Q_('16700 psi')  # 304L SS allowable stress
SS304.nu = 0.3  # Poisson's ratio
SS304.T_min = Q_(-425, u.degF)

SS316 = Material('316SS')
SS316.S = Q_('20_000 psi')  # Table A-1 316 bar
SS316.T_min = Q_(-425, u.degF)

copper = Material('copper')
copper.S = Q_('6000 psi')
copper.T_min = Q_(-452, u.degF)