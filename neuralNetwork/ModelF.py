### Code below is for when number of components = 4.
### The code ModelF takes input x of dimension Q x 7 and returns output y of dimension Q x 5 where
### Q is the number of samples.

import numpy as np
import pandas as pd

def ModelF(x):

    x = np.array(x)
    Q = len(x)

    if len(x[0]) == 7:

        Tmin = -170 + 273.15;
        Tmax = -130 + 273.15;
        Pmax = 700;
        Pmin = 100;

        x[:, 4] = (x[:,4]-Pmin)/(Pmax-Pmin)
        x[:, 5] = (x[:,5]-Pmin)/(Pmax-Pmin)
        x[:, 6] = (x[:,6]-Tmin)/(Tmax-Tmin)

        x_xoffset = [[0.798793470546487],[0],[0],[0],[0],[0],[0]]
        x_gain = [[9.94003527336861],[20.7619047619048],[40.9075630252101],[20.2539682539683],[2],[2],[2]]
        x_ymin = -1
        x_xoffset = np.array(x_xoffset)
        x_gain = np.array(x_gain)

        # Layer 1
        b1 = [[4.5320112894982571561],[12.311559182343827956],[11.104030490756342076],[-0.77318493339851190882],[-0.8501347423583528462],
              [-0.85181370636652498085],[-3.1502992625376582403],[0.60466356492329564887],[0.49456981641304537112],[-17.141433777165943297]]
        b1 = np.array(b1)

        IW1_1 = [[-1.8775400758775999677, 2.8449463212296688397, -2.0453590671988908234, -1.181458812846957418, 1.0302457349998406233, 2.1796507316162507806,
                  1.2793592445574488714],[-2.1273967009412464435, -0.91395642694297141162, -0.44603584027877751783, -0.85881010569239890629,
                  -5.2373078706292606199, -0.36558278709231567527, -7.1267323356253839961],[-1.3464575243076088995, -1.2487989637530689802,
                  -0.21273387379098007699, -0.82557532631287067204, -7.0544400209363748999, -2.6034752558894957986, -6.8464474456637143263],
                  [0.99999227085442254914, 0.59410394267728205975, 0.25035629500509298806, -1.4914675400669277217, -3.618584785152920702,
                  5.3617344622956064626, -2.279912889534366105],[-0.12531778900980033997, 0.0042661001940502195698, -0.043213223934734597276,
                  -0.15849584909419825451, 0.20581381972189585761, -1.5829769368887536274, -1.4444435606551713214],[-1.1434582074766148629,
                  -0.51206283610834091302, -0.27390032722178042635, -0.73854067080296970094, -0.37090762760487816507, 0.91281439218607218766,
                  0.027803132957214298643],[-0.20712736903298586966, -0.081748779194906126544, -0.059720760676493865604, 0.020878018795805239338,
                  0.19516584680594364909, -2.8465824754675717045, -0.2867314906118695883],[0.52323241739164860764, 0.20708478342751204804,
                  0.12237750878473403759, .50147975017286738897, 1.0668603299318699662, -1.2375142824739955305, -0.50644282953945618519],
                 [0.63630109956183433795, 0.43853273015319060857, 0.20613662829881437832, 0.51093442939768551891, -1.4152822999210272759,
                  1.6124214843154029975, -0.34238668841941671817],[1.4616245410654074011, 0.83716397005928755437, 0.42739245160835043214,
                  0.91302534303262228299, 10.781525953077411017, -0.26774228677612083027, 8.8414565638451279028]]
        IW1_1 = np.array(IW1_1)

        # Layer 2
        b2 = [[0.59903065560091617314],[-0.44240674342886648907],[0.56330706028713584121],[0.86474580227935804455],[-0.86505389916554498164]]
        b2 = np.array(b2)

        LW2_1 = [[0.004756210222566697142, 0.73549714531607357504, 0.037331058868100383541, -0.10726126248984338418, -0.10392352931921777781,
                  4.6360843036949450635, -0.28334076463791263434, 2.579179876508687741, -0.14786573478732586984, 0.53104196329557196155],
                  [0.0043885315487953721961, 1.21602182949130877, -0.09030457998506598305, -0.037670698696653494297, 0.022370493533496779714,
                   1.1022510475970874744, 0.14735335965478557618, 0.53987517689764086271, -0.19037656034028163643, 1.1548973608357899767],
                   [-0.37643706885153693786, -0.95877012200434497124, 0.025804610118018839887, -0.082161820385206002504, 0.056052642042756936624,
                    0.48624140792832926117, -0.29688839488957219359, -0.69547249269869260146, -0.73240374117381024099, 0.0014812915499626240837],
                    [0.5319760811219749197, -0.11798462661708834787, -0.3571540286436120093, 0.46094534966476879978, 0.069502448621276233243,
                    0.99056391570613600006, -0.32642425235591615573, -0.78698133960271376974, -0.41528064505205491974, 0.8517262951979228669],
                    [0.032166465877754291114, 0.24574436385264805671, -0.27778988079849870063, -0.18864562985709745768, -0.42248229058349529019,
                     -0.37648124722598008685, 0.79702199010950236513, 0.81847186599752608238, 0.26334791405819518717, 0.088050195548946649793]]
        LW2_1 = np.array(LW2_1)

        # Output 1
        y1_ymin = -1
        y1_gain = [[0.0400285202623229],[2],[105.086695070484],[3245.56319732009],[20.2556065049809]]
        y1_gain = np.array(y1_gain)
        y1_xoffset = [[102.33557940717],[0],[0],[0],[0]]
        y1_xoffset = np.array(y1_xoffset)

        x1 = np.transpose(x)
        x1 = x1-x_xoffset
        x1 = np.multiply(x1,x_gain)
        xp1 = x1+x_ymin

        a1 = np.repeat(b1, Q, axis=1) + np.matmul(IW1_1, xp1)

        a = 2 / (1 + np.exp(-2 * a1)) - 1

        a2 = np.repeat(b2, Q, axis=1) + np.matmul(LW2_1, a)

        a3 = a2 - y1_ymin
        a3 = np.divide(a3, y1_gain)
        a3 = a3 + y1_xoffset

        y1 = np.transpose(a3)

    elif len(x[0]) == 8:

        Tmin = -170 + 273.15
        Tmax = -130 + 273.15
        Pmax = 700
        Pmin = 100

        x[:, 5] = (x[:, 5] - Pmin) / (Pmax - Pmin)
        x[:, 6] = (x[:, 6] - Pmin) / (Pmax - Pmin)
        x[:, 7] = (x[:, 7] - Tmin) / (Tmax - Tmin)

        x_xoffset = [[0.756588072122053], [0], [0], [0], [0], [0], [0], [0]]
        x_gain = [[8.21652421652423], [22.1333333333333], [43.0924369747899], [21.6129032258065], [22.112], [2], [2], [2]]
        x_ymin = -1
        x_xoffset = np.array(x_xoffset)
        x_gain = np.array(x_gain)

        # Layer 1
        b1 = [[-0.44261197919553946223], [19.037572951279077671], [0.52850135945660503545], [-1.6338527443398058736],
              [-4.8413400277463800592], [6.9231778484419184139], [-2.8797418994013188609], [-0.4320836861356147085],
              [-0.6889285776873416145], [-5.445586760122003156], [18.781492290006340795], [5.2590316430468631026],
              [15.981879102599375386], [6.1008062214486553643], [27.905987535160573287]]
        b1 = np.array(b1)
        IW1_1 = [[-0.39416965841887041666, -0.16018619396533842481, -0.095757516425701377782, -0.13096437920267534061,
                  -0.098603921130058586053, 0.30752693099471700711, -0.39610911860923592176, 0.51935817039622977909],
                 [-3.6158467544282211215, -1.3473415403008730529, -0.74242994525477201684, -1.4006206983362528007,
                  -1.7972996413502480006, -11.863564466890542448, 0.46970718908458375385, -11.631026935016818058],
                 [0.27236792021122219198, 0.098361687792542784603, 0.072986723676142076234, 0.070937142730202518148,
                  -0.17375713075056281598, 0.3773460790054642966, 0.24232554554734603292, -1.1590402559007073613],
                 [0.35059695886293446021, 0.1300270121496541198, 0.043081858902724673444, 0.098933395334761684015,
                  -0.9611990490083847094, 0.72268126903790330662, -0.017368874057085405271, 0.65857244598291997395],
                 [1.9856337655965425881, 0.745709600659850258, 0.39760227085377031209, 0.71673520219667141706,
                  -2.9148700350246583568, 0.25872069297229965956, 0.2446755621187755303, -0.5043133851789650679],
                 [-1.7928514085204436679, -0.3163096188857998925, -0.00036052968079960988693, -0.4095322633689163494,
                  1.00718920269799872, -4.3868351607666866698, -0.17854517516419785017, -2.5857968023805741886],
                 [1.1987416954155798443, 0.43424675791265981983, 0.23064321211917837573, 0.46212585721630355939,
                  0.40792435520179770592, -0.50270491792229166084, -1.3759735505173558145, 0.48755382618390369354],
                 [-1.2862693420788728904, -0.49633496595723919365, -0.22899881394838275672, -0.49668263615645924514,
                  -0.33301264094190202725, 0.159572905504333451, -0.21130869558589077117, -0.6757540519051628003],
                 [-0.97523866914541557094, -0.36649776248998483519, -0.2073426929250692663, -0.34456723286283219565,
                  -0.2153198623127722533, -0.11946171309117600834, -0.31079667285344858563, 0.91567619137821398834],
                 [2.7064018520809622892, 0.73913424134262317722, 0.2919957213573106114, 0.85843329878846219572,
                  -0.21110531143883035088, 1.9855711620618057278, 0.079014860879165316199, 3.8129435436172838259],
                 [-3.4666784142158766358, -0.96049434438091418897, -0.65864752726786701675, -1.2961476266401983359,
                  -1.5770393565142872827, -12.652680940899537987, 1.1447407343477546959, -11.505699269921979777],
                 [-0.37991220776367723433, 0.21246423767470601351, -0.10622825718092916703, -0.13153501738234898988,
                  -0.16568254313145741596, -1.2761710578748395317, 1.2110921897282693749, -2.6037766220786493498],
                 [-4.0822684197160139519, -1.3005583368753268481, -0.80692363690087831607, -1.55602556133367953,
                  -1.9298638425970229271, -10.642479803456261322, 1.0486857622725742623, -10.010236000879224605],
                 [-2.2499543868604656716, -0.53034904079554734402, -0.14986369455448048105, -0.63692280703360193428,
                  0.60585317778801939248, -2.6551182690503152273, -0.13127622523602458515, -3.6490139810620836336],
                 [-11.971052975046436728, 14.612493932156139564, 4.0038358219273524341, -1.9215023753841267151,
                  -2.0598211391151766136, -3.0041879481470967761, 6.926062278869363098, -4.4737336338924373891]]
        IW1_1 = np.array(IW1_1)

        # Layer 2
        b2 = [[-0.60970781689065167708], [-1.5288130063898828226], [0.54739397546244572546], [-0.79635322450436396569],
              [0.10363906780771867111], [-0.094539503066484079086]]
        b2 = np.array(b2)
        LW2_1 = [[4.2948405502745705675, -0.68314347581817647104, -3.8805993519667625336, 0.23752210448248073371,
                  3.5283187123164441168, 3.2342571826411874447, -4.1592252660436308531, -0.77803793946757193734,
                  -8.531981736174316211, -5.2410767028521574318, -0.31962779701473581495, -0.34596401355272043965,
                  0.54181222114792126909, -7.9892905460329961542, -0.032932690135208816939],
                 [-0.56534061249512435054, -0.96709683742383356631, 0.533268069595460803, -0.12709492224734258992,
                  -1.9104455509278011061, 1.7236818534010589499, 0.50744573001879600405, 0.073556528955692257465,
                  1.4644318623120862188, -2.3630153215160003555, -1.1054614873013455245, 0.12243145010531081285,
                  1.4319678480803694764, -4.2126490273288696997, -0.013896645692304532282],
                 [-0.018453752501723479085, -0.42587883348622923574, 0.039900106167820435787, 0.037227299307598819833,
                  0.55128351659308172383, 0.31894985572097034332, 0.64059612761098805311, 0.035917149639324366661,
                  0.084099310407628136144, 0.66431550439446973577, -0.38145903978397927014, -0.13114296483174955887,
                  0.47925346487686232289, 0.38310978630681791213, 0.083354665626464222172],
                 [-0.37178935282242614457, -0.089864826612976733688, 0.81228978830640796716, -0.63579946751813343209,
                  0.14854764677308859855, 0.45063571924178369432, 0.42351312912319316606, -0.55431909469265716606,
                  -0.66094644966815052634, 0.71307112354113388886, 0.19308232984718973202, -0.031021708996637090833,
                  0.57443867802055725846, -0.64299354805131014867, 0.068118682357881571443],
                 [-0.64163768675681276399, -0.14078599518732470841, 0.1687327706745423983, 0.12115615848253331877,
                  0.29046521285256365896, 0.93428787639590571423, 0.32094647261631653601, 0.29216610853046426355,
                  1.1521721041328099044, 0.65326123847094452746, -0.20996159599955732666, 0.26708623725867042253,
                  0.32565173003303521382, -0.43224678266661781256, 0.39594339894461960672],
                 [-3.2338556110443970049, -0.14237266597767347931, -3.2449325087002964807, -0.10703454897750838692,
                  -0.16810542533116185071, -0.32229414124461364111, -0.15149367652833559128, 0.99229017302229149955,
                  1.1294098789316939779, -0.35012030667269250506, -0.15055697422321817625, 0.37022372529532449059,
                  0.33854755536994868281, 0.015319474629976058758, -0.053207422045798001553]]
        LW2_1 = np.array(LW2_1)

        # Output 1
        y1_ymin = -1
        y1_gain = [[0.0330957027727313], [2], [65.5780736278755], [1289.77012541715], [21.6140777882657] , [22.1120442396484]]
        y1_gain = np.array(y1_gain)
        y1_xoffset = [[90.167369648934],[0],[0],[0],[0],[0]]
        y1_xoffset = np.array(y1_xoffset)

        x1 = np.transpose(x)
        x1 = x1 - x_xoffset
        x1 = np.multiply(x1, x_gain)
        xp1 = x1 + x_ymin

        a1 = np.repeat(b1, Q, axis=1) + np.matmul(IW1_1, xp1)

        a = 2 / (1 + np.exp(-2 * a1)) - 1

        a2 = np.repeat(b2, Q, axis=1) + np.matmul(LW2_1, a)

        a3 = a2 - y1_ymin
        a3 = np.divide(a3, y1_gain)
        a3 = a3 + y1_xoffset

        y1 = np.transpose(a3)

    return y1
