USE TULIPTHECLOWN;
INSERT INTO Contact (contact_id, name_, xor_key, contact_type, phone_or_email)
VALUES
(
0x5f39b51ae9a4dacbb8d9538229d726bf,
0xf33dab,
0xb952c5,
0,
'none'
),
(
0x2e7041b7d708dfe8714bc27f4a0e3393,
0x140c443e9038fb8532,
0x5764254cfc578ff1,
0,
'none'
),
(
0x8f0ac432bd330d8bde1d3378dc86ad67,
0xa82f3549f0d83f,
0xe64e41289cb25e,
0,
'none'
),
(
0x5c9ebdaf3ca35bffbdd82ce5091be9dc,
0xa4083374830b,
0xe969411ded6a,
0,
'none'
),
(
0xc5aaaa827168730cfb4df279514e841a,
0xd8bfb88211,
0x91cdd1ec70,
0,
'none'
),
(
0x135901c2b25beb3656f52082872b3d2d,
0x0e204ae7911fa8,
0x5a413e8ef071c9,
0,
'none'
),
(
0xc229f65d540f2ffd58f9186ec1a05d0f,
0x8522eacdf3fb,
0xca4999ac9d9a,
0,
'none'
),
(
0xb690076285257a2f2eb798a3f5d2a632,
0x6b6cb55578787d,
0x2a00dc3611121c,
0,
'none'
),
(
0x6515c69e3b95305f8506432a2b7725a5,
0x8ba8ca059245bcc4a0,
0xc1cdbc62f72bd5ae,
0,
'none'
),
(
0x38c0855599a222b4f96bc49aa93641af,
0x64ae5481ea,
0x37d831f58b,
0,
'none'
),
(
0x9c2d29850e7fd884c19b3ef48a01b82c,
0x3de37246,
0x728f1527,
0,
'none'
),
(
0x4b7b1ac66589f1ab84eb0690060a44fb,
0x747d09f1a97cabcd5c72,
0x35136882dd1dd8a4,
0,
'none'
),
(
0x8fd3e79e1aba2d20f66427cd4095ce15,
0xff2e30b0fbafd6f4f52d,
0xb06277f1db89f6b8,
0,
'none'
);
INSERT INTO Review (review_id, contact_id, review, xor_key, weight, response, creation_time, response_time)
VALUES 
(
0x48ab760cd9a9a1d4e0eef02e65694bcf,
0x5f39b51ae9a4dacbb8d9538229d726bf,
0xe2ba66d13d0650ee7e8c74c2b5d150c0d0ba6698630809af7ec4668db9d950c596bb62dd6d4d4eeb7e8c62dabacc15c5dfbb6298254355af79de6aceb0c615d3d8ab2acb204f4bea2c8c54c8fcc75092c4aa6bd4215f07ff61c962debed115c5d3ef68d7224d42eb2dc466dffa,
0xb6cf0ab84d26278f0dac03addbb535b2,
1,
0x5468616e6b20796f752076657279206d756368204a6f686e212049276d20676c61642065766572796f6e6520656e6a6f79656420697420616e64207468616e6b7320666f7220626f6f6b696e67206d652e,
'2017-02-10T13:42:00',
NOW()
),
(
0xc9d53e84b28537db148f4a985a050743,
0x2e7041b7d708dfe8714bc27f4a0e3393,
0xfd279bdc0a125aceecf0ce97ec9e8e04d16ec193634658daf1efce99e285da07da3c95882b5b439bf2eb9c8ee49e9d41986ed4902f1244d3faa48d88e49c9e13d0209594225610dabfe28f8ef9918915dc2d95882a5f559bfeea8ac0ff959b0dd93795992d585fc2fae0ce81e19cda15dd2b959b225f55c8bfe58084ad809313d43ad0dc225144d2e9ed9a89e883db41f62fc588225b5e9bd0e88289e8d09200d16ed993374110d4f9a48895e3d00afe2ccc95a82b535ed0eca48f87ec999441d420d1dc0a1258d4efe1ce99e2858841df21c08e2d57499bfde58d8bad849541f921db982c5c10ccfef7ce95e3958c04db3ad3892f1c10f9faf79ac0fa998909d03d95bf2b5342d7f0f09a85,
0xb54eb5fc433230bb9f84eee08df0fa61,
1,
0x205468616e6b20796f7520436861726c6f74746521204361707461696e204f6c6c696520697320612067726561742070697261746520616e64204920686164206c6f7473206f662066756e206174206869732050697261746520426972746864617920706172747921,
'2017-02-25T14:45:00',
NOW()
),
(
0x628f4f5914bea2eda72c0fe976d13c34,
0x8f0ac432bd330d8bde1d3378dc86ad67,
0x7a831e6307f1e4cb0b9dd7a466097f5740c2266d05ffea854da6cce9312d6d04599b4a660aeee29f058acaee356c2b505cc2086b19efed8f0c9698b9273e6a5d148304664bd2a581189ccce9312d705051864a7604bbf68a14cfd9e924257904408a0b6c00e8a59f02cff3ba232277451ac23e6a0ebbf58a1f9bc1e9312d6d04558f0b7802f5e2c54da6cce9312d6d045d8c1e6719fae69f0499dde927227a045297042c,
0x34e26a026b9b85eb6defb8c9464c1e24,
1,
0x5468616e6b20796f752076657279206d75636820666f7220696e766974696e67206d65212049276d207665727920676c616420746861742065766572796f6e6520656e6a6f7965642069742e,
'2017-04-04T07:43:00',
NOW()
),
(
0x11e18eaa772b32ad67ede3ec9c8aff84,
0x5c9ebdaf3ca35bffbdd82ce5091be9dc,
0x171afedbd99dd270caa528e605f5cc8a2652f8c7d7dcdf3fcbec23ec57a1d0876319f6d1c19dc37ec9e06ee116b196c21417bfd4ded18b77def32ba912bbd28d3a17fb95cbd2de6d9fe020fd12a7cc832a1cf2d0dcc9853fe6ea3bae01b0988f2216fa95c6d5ce3fcfe43cfd0ef5cb922611f6d4de93,
0x43729fb5b2bdab1fbf854e8977d5b8e2,
1,
0x7468616e6b20796f7521204d696c616e612773207061727479207761732067726561742066756e20616e6420697420776173206c6f76656c7920746f2073656520746865206b6964732068617070792e,
'2017-04-30T22:35:00',
NOW()
),
(
0x3dc64cb7f25c37ae1652537949ca000e,
0xc5aaaa827168730cfb4df279514e841a,
0x70d3102839124f7707d8178719fb9a2a55d81a7a603649321fd41c9f15b6bb215c9617356b795d321ede008250a9a83758960533743c12322ad9078a51a9ab2c14d71329763549660cdd17c659b4b8275096182e3938527649f84e8b40a8ba6255d21c336d794c731bd4009246fbaf3114c1143675781c450c91198347beee2155c605336f3848770d910c9f15afa62714d5193b6b34557c0e9108875ca9b76255d8157a6d31593204d8038315bdbc2d599605327c795a7b1bc21ac658b2a03740d3513b773d1c7b1d91198746fbbc2755da1d23392a5d7649c501c659beba624dd9047a7e361c731d911a8e50fbab2c50964b7730771c5e06de058f5bbcee245bc4063b6b3d1c6606911d8350b2a02514cf1e2f39385b7300df40c677bebd361896382870375d,
0x34b6715a19593c1269b16ee635dbce42,
1,
0x205468616e6b20796f752076657279206d756368204972696e6121205765206c6f766564206265696e6720617420417274656d277320426972746864617920706172747920616e6420686164206c6f7473206f662066756e206f757273656c7665732e,
'2017-05-02T08:31:00',
NOW()
),
(
0x175a3118470f9ace7d9222c37b0a4ef9,
0x135901c2b25beb3656f52082872b3d2d,
0x707f918ea49e9e5d5613d8016d12796c5a71d085eba0cd4b575ad4582e0e316b5b68d09da4b29f5d590e995d2c146574183a9e93f0f582565403994b221431624168d097edb19e185a0fcd0d2c0a6262147c9f8ea4a1855d180ad85f2808657e143bd0abe1f585595c5aed58210f612d407295dce7b9824f565ad8412208762d43738494a4b4cd5b5715d50d1d0f636c407fd094eba69951561d99423814313f1463959df6a6cd57541e995e2208367e1478998ef0bd8959415ad84329467879146d918fa4a68218550fda456d006463183a8494e1f58c5b4c13cf44390f747e146d958ee1f58b514c0edc496d127e2d5c7383dce5bb89184c12dc0d2a13747e4069d09de3b0c04a5914de486d0464791475858ea4b38c4e5708d0592846666c473a8494e1f58f595416d642234670635d779190f7f58c565c5aca593800772dc4856875a481a579763199740233312c153ad1dd,
0x341af0fc84d5ed38387ab92d4d66110d,
1,
0x446561722054617469616e612c207468616e6b20796f752076657279206d75636820666f7220796f7572206b696e6420776f72647321205468652050697261746520616e6420492068616420616e20616d617a696e672074696d652061742056616e7961277320626972746864617920616e6420656e6a6f7965642069742076657279206d75636820746f6f21,
'2017-05-21T17:24:00',
NOW()
),
(
0x2e38f106115c9d06be48e1781b55d42a,
0x135901c2b25beb3656f52082872b3d2d,
0xace50b015177f134292053a4bbe5328dd4ad0c004877e97b3a791dd0a6e637949cec134f5c38fa7b337901d0eceb3e988baf44,
0xf88d6a6f3a57885b5c0c73f0ce895bfd,
1,
NULL,
'2017-12-04T15:21:00',
NULL
),
(
0xa2a6a1fa3d7cab40eaef40e090562a65,
0xc229f65d540f2ffd58f9186ec1a05d0f,
0xcff2a616a7e8cedb21a88271e8806a15e5fce71de8d69dd820b3c33ee8b2771aabe7b50de9c0d8cd3ce1933ebaa07b5aabdeb344f0c2ce9e22b8c33ba9a1651cfff2b543f48389ca27e18136baa06a10eaeee944d4cbd89e38a0907fa9ba6654e2fab716e2d0cedb2be19730a4b02211fdf2b51de8cdd89e3ba9822be8916e07eab7af05f483ded122a4c32ba7f46a11f9b9e730efc69dce2eb39726e8a36307abfea910e2d1dcdd3ba8953ae8b56c10abf1b20aa983f1d120aa8a31aff4641bf9e0a616e383c9d16fb2863aa1ba6554f2f8b244e6c4dcd721efc338a7bb6654e7e2a40fa9,
0x8b97c76487a3bdbe4fc1e35fc8d40274,
1,
NULL,
'2018-12-05T09:51:00',
NULL
),
(
0xaeafbc95f8481e4e721352bff0b14eda,
0xb690076285257a2f2eb798a3f5d2a632,
0xf35d843adefcbdbc1636da0a0fc3e666cf50c53bc7e8fc990c29d5170ccda832ca4cc530d4fafa9f1136c64328cda87bcc54d374d7e6ef830d37d51a45d2a760d34ccb17dde6f1931736da4313c7b46b875d8424c5f6b3d795cc2cee,
0xa735e554b58f9df76553b46365a2c612,
1,
NULL,
'2018-12-25T20:45:00',
NULL
),
(
0xbb28a19a764ddb57372473fdcea0356a,
0x6515c69e3b95305f8506432a2b7725a5,
0x2072fdbde94be38872605f7685e5385a635fb7f8be46f49f75605279d7fc291e6647e0bfa15de3892860697792b138516e4ff1b9b009f28e742e587bd7fe254a2252faf8ab4ca68d6332443f91e43e1e6348f1f8a047f29e74254e6b9eff37102267f9b4e95dee9e2627487a84e5231e7543e7bde94de3976f27556b92f5705f6c42b5bdbf4ce8db6724487383e270ce9dbf17f88448e8822624547991f4225b6c52b5bba647f29e75344e33d7fc31596b45b5acbb40e590756c1d7d96fd3c516d48e6f8a847e2db6b355e77d7fc3f4c6707b58fa647e29e74264873d7c935506b47b5b0a84da69a26274f7a96e570566d4afcbca850a7db5228586d92b1275b7043b5bba140ea9f7425533f98f7705a6b40f3bdbb4ce88f26215a7a84b1314a2252fdbde959e78972391d7e99f5705b7443e7a1a647e3db71214e3f81f42247224ffbacac5be38872255931d7c5385b7043b5afa85aa69a262c526bd7fe361e6453fbf8a847e2db7228583f94f939526654f0b6e94def9f262e526bd7e631507606e1b7e945e38f2627523f98f7704a6a43b5afa647e29e74264873d7d73157705fb4f839b61e78260b4e7a99f8311e764ef4b6a209ff9473604b7a85e870537745fdf8af46f4db75355e77d7f6225b6352b5b5ac44e9896f254e31,
0x022695d8c92986fb06403d1ff791503e,
1,
0x457667656e6979612c207468616e6b20796f752076657279206d75636820666f7220796f75722072657669657721204974277320677265617420746f206865617220746861742065766572796f6e6520656e6a6f79656420697420f09f8c9e,
'2019-06-21T08:26:00',
NOW()
),
(
0xb1e9d61c483fd0416b77da3b8edda530,
0x38c0855599a222b4f96bc49aa93641af,
0xb855f7a1caa5493b24084fd90b2541bf925eb2f18ea5403f370e45d9022657bf9b46e7a7d6f15c28785c7e900a225fe6df55f7a3d1e8543f3818539d,
0xff2792c0be85395a567c36f96d4a339f,
1,
NULL,
'2019-10-09T08:23:00',
NULL
),
(
0xa8dabebe726e69f043e8f0cb326490e4,
0x9c2d29850e7fd884c19b3ef48a01b82c,
0x264a0e378f3785c00557837d0446ae4517431f659a7680d50f5798670607a75e08470f658c788081190285351209a7173d4e02338f65de81011f98350815e900525b0e249864d2ce1a13d935350eac4517021c209872d2c0561b98614109af1715430620993793cf1257947a0c16ac431b56022a8464dc8137199335150eac17114a02298e6597cf560092670446bf52005b4b2d8b6782d8561699714103b1541b560e21c437a6c9130ed7610e0aad17064a0a31ca7e868101168435150eac1715500e249e7281d55613966c4109af17064a0e2c98379ec81012d93591f951be526a0222827b8b812412947a0c0bac5916470f64cb,
0x72226b45ea17f2a17677f7156166c937,
1,
NULL,
'2021-07-14T23:25:00',
NULL
),
(
0x3605568d7da9184a49fe51a19722a742,
0x4b7b1ac66589f1ab84eb0690060a44fb,
0x4a0393dabfff3a055e42c665eb51ec096e0293c7bbeb2f1e0a48d821ac028d14635ad5d1acaa29054f07d22cf051b85a7313dedbfefd384d4e42d72ce647a85a731593dfade17d0c4407d52beb4fad0e680893d8b1f87d054f4bc46ba269bf1f6913d29ea9eb2e4d494fdb36e74cec186219d2cbadef7d1e42429436f24da71f2728c6cdade33c030607d52be602ad166b5ac7d6bbaa3a04584bc765e356ec0e6f1f93cebff829140a50d137e7029e0f7409dadfb0a47d265942da2ce302b815681193d7b0fe324d4b44d72af74cb85a6616df9eb3f37d1a4354dc20f10cec3b745ad29eb3e529054f559865cb02ad16741593c9bfe429084e07c02aa252ad087313d2d2b2f37d1d4b55c02ce14bbc1b731f93d7b0aa3a0c4742c765f54bb8122719dbd7b2ee2f0844099404ec46ec1f711fc1c7aae234034d07c32af049a91e2715c6caf0aa14190a50d536a243ec16680e93d1b8aa3b1844069564a263a21e2717ca9ebbe6390859539421e357ab12731fc19ebbfc38030a50c62af647ec1b2709c7d1acf37d044407dc20f002a8136608ca9eaae2384d4442cc31a246ad03271bd5cabbf87d194242942ded4ea51e660393dfbce528190a4fdb32a24fb9196f5ad5cbb0aa29054f5e942de346ec0e6f1bc79ebaeb24430a73dc24ec49ec03680f93c8bbf8244d4752d72da269bf1f6913d29ffed332180d55d165f047ad166b0393d9acef3c190b07f92af156ec15615ad2d2b2a67d0e424ed821f047a25a751fdedbb3e8381f0a4ad522eb41ec0e7513d0d5ada67d194242cd65f156a5166b5ad0dfb0e432190a52da21e750bf0e6614d79eb6e52a4d43539424ee4eec12660ac3dbb0ef394ddab82dc7a26aa51d6f16ca9eacef3e02474ad12be618e5,
0x077ab3bede8a5d6d2a27b4458222cc7a,
1,
NULL,
'2021-11-16T21:22:00',
NULL
),
(
0x7a59aa4daf42e57fda10198212e68028,
0x8fd3e79e1aba2d20f66427cd4095ce15,
0x8850c7a84498369de3c0e998af9c9a45ae58cce0498f72cde7cafd84fc869d5ea54bc5b35c88788ab1cae189b99d874ba957c5b206c14188b1cefd98fc869d5ca94dc9ae4fc17e88e38ffc98bf809d4ee04dc9ad4dc17781e3caee99a5cf9545b219cfb55ac17585f8c3eb8fb981dd0a9351c5e04192368ee3caee89b581940ab451c5e04f93738ce5cafc89fc9c9b45b719c6af5ac17d84f5dcaf9cb28bd34ba44cccb45bc17983b1c0fa8ffc9f9258b4408ee06b897f81f5ddea93fc8e814fe04acfe04080669de883af9cb28bd35eaf55c4e05d923699f9cefbdda8879a59e04ec1b308957e88b1cdea8ea8cf974bb919cfa608957e88f8ddaf91b5899604e0c93f58a1c14582bd8fc794bb879f53e06bc5a3478c7b88ffcbea99fc9b9c0aa157d9e04e807b84fdd6af8ab59b9b0aa351c9ac4c937383b08eaeddf4dfca07f00c8df218d324c4,
0xc039a0c028e116ed91af8ffddceff32a,
1,
0x5468616e6b20796f752076657279206d75636820666f7220796f7572206b696e6420776f72647321204974277320616c776179732067726561742066756e20746f20656e7465727461696e20796f7572206368696c6472656e20f09f988a,
'2022-05-18T21:49:00',
NOW()
);